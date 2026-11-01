# Twitch chat ingress

This P-056 worker reads `channel.chat.message` notifications from Twitch EventSub WebSockets and
forwards a validated `chat` event to the existing authenticated backend boundary. The host sees
viewer text as bounded content. Messages cannot choose commands, OBS actions or game input.

Set `TWITCH_CLIENT_ID` and `TWITCH_USER_ACCESS_TOKEN` outside the repository. The WebSocket
subscription uses a user access token with `user:read:chat`; update the numeric broadcaster and
chat-user IDs in `configs/local/twitch-chat.yaml`. If a separate bot account is introduced, apply
Twitch's additional current bot/broadcaster authorization requirements.

Run a safe configuration check:

```bash
PYTHONPATH=modules/backend-api python -m twitch_chat --validate
```

With the backend ready and `AUTOPILOT_BACKEND_URL` plus `HCP_API_KEY` set, remove `--validate` to
connect. Notifications are not replayed after a lost socket. The worker subscribes again after an
unexpected disconnect, follows Twitch's supplied reconnect URL, bounds frames and queues, and
passes Twitch message IDs through for downstream deduplication.
