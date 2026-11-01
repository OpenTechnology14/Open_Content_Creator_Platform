# hcp-alerts — Webhook Alert Overlay

Receives donation, follow, and subscription events via webhook and renders
animated alerts in OBS.

## Setup

1. Configure the webhook URL in your alert provider (Streamlabs, StreamElements,
   or custom): `http://localhost:9091/bundles/hcp-alerts/webhook`
2. Add a Browser Source in OBS pointing to the alert graphic
3. Test with the dashboard "Send Test Alert" button

## Replicants

- `alertQueue` — array of pending alerts
- `currentAlert` — the alert currently displayed (or null)
- `settings` — duration, animation style, sound enabled

## Files

```
hcp-alerts/
├── package.json
├── extension/
│   └── index.js        # Webhook listener + queue manager
├── dashboard/
│   └── alerts.html     # Test buttons + settings
└── graphics/
    └── alert.html      # Animated alert renderer
```

## Status

Scaffolded — skeleton in place, ready for implementation.

## Donation / alert overlays — two paths

| Path | Trade-off |
|---|---|
| **Streamlabs / StreamElements alert pages** as an OBS Browser Source | Zero work, zero control |
| **A NodeCG bundle with webhook ingestion** (this one) | Full control, more work |

This bundle is a **skeleton** for the second path — webhook in, replicant out, graphic renders.
Take the first path if you only need standard alerts; take this one when alerts must react to the
same state the rest of your graphics package uses.

