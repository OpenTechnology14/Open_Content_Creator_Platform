# Multi-Platform Streaming — Decision Guide

OBS can only stream to one RTMP/SRT endpoint natively. If you need to go
live on Twitch + YouTube + Kick simultaneously, choose one of these options.

## Option 1: obs-multi-rtmp plugin (local fan-out)

**Install:** https://github.com/sorayuki/obs-multi-rtmp

- Pros: Free, no third party, no latency added.
- Cons: Each additional stream multiplies your upload bandwidth and CPU/GPU
  encoder load. 3 streams at 6 Mbps = 18 Mbps upload minimum.
- Best for: Creators with ≥50 Mbps upload and a strong encoder (NVENC).

## Option 2: Cloud relay service (Restream / Castr)

**Restream:** https://restream.io
**Castr:** https://castr.io

- Pros: One outbound stream from your machine; the service fans out to all
  platforms. Lower bandwidth requirement.
- Cons: Monthly cost ($16–49/mo depending on tier). Adds ~200–500 ms latency.
  You're trusting a third party with your stream.
- Best for: Creators with limited upload or who need 4+ simultaneous platforms.

## Option 3: Self-hosted relay (NGINX-RTMP on DO droplet)

Run NGINX-RTMP or SRT Relay on a DigitalOcean droplet. OBS sends one stream
to the droplet; the droplet re-publishes to all platforms.

- Pros: Full control, no monthly SaaS cost (just droplet cost), low latency
  if droplet is nearby.
- Cons: You maintain the relay. Requires Tailscale networking ([`infrastructure`](../../infrastructure/setup/manual.md)).
- Best for: Technical creators who are already running a DO droplet.

NGINX-RTMP config will live at `modules/infrastructure/digitalocean/nginx-rtmp.conf`
when implemented (deferred until [`infrastructure`](../../infrastructure/setup/manual.md)).

## Recommendation

Start with **obs-multi-rtmp** if your upload bandwidth allows it. Move to a
cloud relay only when bandwidth becomes a bottleneck or you need 4+ platforms.
