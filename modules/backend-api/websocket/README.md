# websocket

WebSocket helpers. The endpoint itself lives in app/routers/ws.py.

## Fanout model

One process publishes to Redis; many overlay clients subscribe. That is why Redis is a hard
dependency of this module rather than an optimisation — without it, `/ws` has nothing to fan out
from and each overlay would need its own connection to the publisher.

Consumers today: NodeCG graphics (via `hcp-starter/extension/redis-bridge.js`), and any mobile or
automation client hitting `/ws` directly.

