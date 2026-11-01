// Subscribes to Redis `overlay.*` channels and pushes payloads into
// the matching replicant. The FastAPI /overlays endpoint publishes here.

module.exports = (nodecg, replicants) => {
  const url = process.env.REDIS_URL;
  if (!url) {
    nodecg.log.warn('REDIS_URL not set — skipping Redis bridge');
    return;
  }

  const { createClient } = require('redis');
  const subscriber = createClient({ url });

  subscriber.on('error', (err) => nodecg.log.error('redis error:', err));

  (async () => {
    try {
      await subscriber.connect();
      await subscriber.pSubscribe('overlay.*', (message, channel) => {
        const name = channel.replace(/^overlay\./, '');
        const target = replicants[name];
        if (!target) {
          nodecg.log.warn(`no replicant for overlay '${name}'`);
          return;
        }
        try {
          target.value = JSON.parse(message);
        } catch (e) {
          nodecg.log.error('bad payload for', name, e);
        }
      });
      nodecg.log.info('subscribed to overlay.* on Redis');
    } catch (e) {
      nodecg.log.error('redis connect failed:', e);
    }
  })();
};
