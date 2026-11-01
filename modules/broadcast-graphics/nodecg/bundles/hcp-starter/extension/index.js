// NodeCG extension entry point.
// Sets up replicants (persistent state) and wires Redis pub/sub so the
// FastAPI backend can drive overlays via /overlays/<name>.

module.exports = (nodecg) => {
  const scoreboard  = nodecg.Replicant('scoreboard',  { defaultValue: { home: 0, away: 0, clock: '00:00' } });
  const lowerThird  = nodecg.Replicant('lowerThird',  { defaultValue: { visible: false, title: '', subtitle: '' } });
  const sponsor     = nodecg.Replicant('sponsor',     { defaultValue: { active: null, rotation: [] } });

  nodecg.log.info('hcp-starter bundle loaded');

  // Redis bridge (best-effort: skip silently if REDIS_URL not set).
  require('./redis-bridge')(nodecg, { scoreboard, lowerThird, sponsor });
};
