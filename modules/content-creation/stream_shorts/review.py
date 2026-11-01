"""Generate a local video-range editor. Files stay in the browser; no server or uploads."""

from __future__ import annotations

from pathlib import Path

from .models import ClipPlan


def write_review(plan: ClipPlan, output: Path) -> None:
    """Write a standalone review artifact with scrub/mark controls and JSON plan export."""
    payload = plan.model_dump_json().replace("<", "\\u003c")
    html = TEMPLATE.replace("__PLAN_JSON__", payload)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(html)


TEMPLATE = r"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Nova · Shorts review</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101827;color:#edf2fa;font:16px system-ui}
main{max-width:1080px;margin:auto;padding:32px}h1{font-size:32px;margin:8px 0}p{color:#b8c6dc}
video{display:block;width:100%;max-height:54vh;background:#000;margin:20px 0;border-radius:12px}
button,input{font:inherit;border:1px solid #52677f;border-radius:6px;padding:10px}
button{background:#b7f7da;color:#102621;cursor:pointer}button:disabled{opacity:.45;cursor:default}
input{background:#1a2638;color:#fff;max-width:100%}input[type=number]{width:130px}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:end;margin:16px 0}
label{display:grid;gap:6px}.clip{display:flex;gap:14px;padding:14px;border-bottom:1px solid #34465c;
align-items:center}.clip span{flex:1}.clip input{width:20px;height:20px}.small{font-size:13px}
#status{min-height:24px;color:#ffe29c}a{color:#b7f7da}
</style><main>
<div class="small">NOVA / CONTENT CREATION</div><h1>Choose the moments worth keeping</h1>
<p id="identity"></p><p>Choose the matching local recording, preview suggestions, and mark your
own sections. Export the selected clip plan, then render it with the local Shorts command.</p>
<p id="editing" class="small"></p>
<label>Local recording<input id="file" type="file" accept="video/*"></label>
<video id="video" controls preload="metadata"></video>
<div class="controls">
<label>Start (seconds)<input id="start" type="number" min="0" step="0.01" value="0"></label>
<button id="markStart" disabled>Mark start here</button>
<label>End (seconds)<input id="end" type="number" min="0" step="0.01" value="10"></label>
<button id="markEnd" disabled>Mark end here</button>
<label>Label<input id="label" maxlength="120" value="My selected moment"></label>
<button id="add" disabled>Add section</button></div>
<p id="status" role="status" aria-live="polite"></p>
<div id="clips"></div><div class="controls"><button id="export" disabled>Download clip plan</button></div>
<p class="small">Sections must be 0–60 seconds long, with a nonzero duration. Suggested scores
measure participation, not entertainment quality. This page never publishes or uploads media.</p>
</main><script type="application/json" id="plan">__PLAN_JSON__</script><script>
"use strict";
const plan=JSON.parse(document.getElementById("plan").textContent);
const byId=id=>document.getElementById(id),video=byId("video");
const clips=plan.clips.map(clip=>({...clip,selected:true}));
let url=null,ready=false,stopAt=null;
byId("identity").textContent=`${plan.show_id} · ${plan.recording_id} · ${plan.duration_seconds}s`;
byId("editing").textContent=plan.edit.enabled?`Editing: ${plan.edit.captions.length} caption cues · ${plan.edit.punch_ins.length} punch-ins · audio leveling ${plan.edit.style.normalize_audio?"on":"off"}`:"Advanced editing is off for this plan.";
function status(text){byId("status").textContent=text;}
function redraw(){
 byId("clips").replaceChildren();
 clips.forEach(clip=>{
  const row=document.createElement("div");row.className="clip";
  const check=document.createElement("input");check.type="checkbox";check.checked=clip.selected;
  check.setAttribute("aria-label",`Include ${clip.label}`);check.onchange=()=>clip.selected=check.checked;
  const text=document.createElement("span");
  text.textContent=`${clip.label} · ${clip.start_seconds.toFixed(2)}–${clip.end_seconds.toFixed(2)}s · ${clip.origin} · score ${clip.score}`;
  const preview=document.createElement("button");preview.textContent="Preview";preview.disabled=!ready;
  preview.onclick=()=>{video.currentTime=clip.start_seconds;stopAt=clip.end_seconds;
    video.play().catch(()=>status("Use the video play button to preview."));};
  row.append(check,text,preview);byId("clips").append(row);
 });
}
function setReady(value){ready=value;["markStart","markEnd","add","export"].forEach(id=>byId(id).disabled=!value);redraw();}
byId("file").onchange=()=>{
 setReady(false);stopAt=null;if(url)URL.revokeObjectURL(url);
 const file=byId("file").files[0];if(!file)return;
 url=URL.createObjectURL(file);video.src=url;
};
video.onloadedmetadata=()=>{
 if(!Number.isFinite(video.duration)||Math.abs(video.duration-plan.duration_seconds)>.25){
  status("Duration does not match this plan. Choose the correct recording.");setReady(false);return;}
 setReady(true);status("Recording loaded. Confirm the recording ID as well as the duration.");
};
video.onerror=()=>{setReady(false);status("This browser cannot decode the recording. Use an MP4 review copy with matching timing.");};
video.ontimeupdate=()=>{if(stopAt!==null&&video.currentTime>=stopAt){video.pause();stopAt=null;}};
byId("markStart").onclick=()=>byId("start").value=video.currentTime.toFixed(2);
byId("markEnd").onclick=()=>byId("end").value=video.currentTime.toFixed(2);
byId("add").onclick=()=>{
 const start=Number(byId("start").value),end=Number(byId("end").value),label=byId("label").value.trim();
 if(!Number.isFinite(start)||!Number.isFinite(end)||start<0||end<=start||end-start>60||end>plan.duration_seconds||!label){
  status("Choose a valid 0–60 second section and a label.");return;}
 if(clips.length>=40){status("This plan already contains 40 sections. Export or start a new review.");return;}
 clips.push({start_seconds:start,end_seconds:end,label,origin:"manual",score:0,unique_viewers:0,selected:true});
 redraw();status("Manual section added. Uncheck any suggestions you do not want.");
};
byId("export").onclick=()=>{
 const chosen=clips.filter(clip=>clip.selected).map(({selected,...clip},i)=>({...clip,clip_id:`clip-${String(i+1).padStart(3,"0")}`}));
 if(!chosen.length){status("Select at least one section.");return;}
 const blob=new Blob([JSON.stringify({...plan,clips:chosen},null,2)],{type:"application/json"});
 const link=document.createElement("a"),download=URL.createObjectURL(blob);
 link.href=download;link.download=`${plan.recording_id}-selected.json`;link.click();
 setTimeout(()=>URL.revokeObjectURL(download),1000);status("Clip plan downloaded; media has not been uploaded.");
};
redraw();
</script></html>"""
