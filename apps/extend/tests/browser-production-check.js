// Assertions run in the explicit synthetic browser fixture; never imported by
// production. These inspect rendered behavior rather than Svelte source text.
export function assertContentProfile() {
  const selector = document.querySelector('select[aria-label="Active content profile"]');
  if (!selector || !selector.textContent?.includes('Synthetic Content') || selector.textContent.includes('Synthetic Stream')) {
    throw new Error('Content profile options retained the Stream workspace after navigation');
  }
  return 'Content profile options belong to Content';
}
export function assertSafety() {
  const buttons = [...document.querySelectorAll('button')];
  for (const label of ['Stop owned recording', 'Mute Synthetic Mic']) {
    const button = buttons.find(item => item.textContent === label);
    if (!button || button.disabled) throw new Error(`${label} disappeared or became disabled`);
    const box = button.getBoundingClientRect();
    if (box.bottom <= 0 || box.top >= innerHeight) throw new Error(`${label} is outside the viewport`);
  }
  return 'Owned recording Stop and input mute remain available';
}

export function assertStartedIdentitySurvivesObservationFailure() {
  const stop = [...document.querySelectorAll('button')].find(b => b.textContent === 'Stop owned recording');
  if (!stop || stop.disabled) throw new Error('Successful Start identity was lost when status failed');
  return 'Start identity retained';
}
export function assertAutomaticSafetyAudio() {
  const calls = /** @type {{fixtureCallLog:{command:string}[]}} */ (/** @type {unknown} */ (window)).fixtureCallLog;
  if (!calls.some(c => c.command === 'production_audio_inputs')) throw new Error('No automatic safety audio call after fresh Start');
  if (![...document.querySelectorAll('button')].some(b => b.textContent === 'Mute Synthetic Mic')) throw new Error('Safety mute unavailable');
  return 'Automatic safety audio available';
}
export function assertInspectionDoesNotBlockSafety() {
  for (const name of ['Stop owned recording', 'Mute Synthetic Mic', 'Refresh OBS status']) {
    const button = [...document.querySelectorAll('button')].find(b => b.textContent === name);
    if (!button || button.disabled) throw new Error(`${name} disabled by inspection`);
  }
  return 'Inspection leaves safety controls admitted';
}
