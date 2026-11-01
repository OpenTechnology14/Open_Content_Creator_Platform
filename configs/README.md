# Configuration Overlays

Environment-specific, non-secret configuration belongs here.

- `local/` contains workstation defaults and examples.
- `digitalocean/` contains cloud overlay configuration.

Never commit credentials, tokens, stream keys, private host details, or generated `.env` files. Add environment variable placeholders to the root `.env.example` and document whether each value is local-only, optional, or production-required.
