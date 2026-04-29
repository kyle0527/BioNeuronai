# Security Policy

## Supported Versions

Security fixes target the current `main` branch unless a release branch is explicitly maintained.

## Reporting a Vulnerability

Do not open a public issue for secrets, exchange-key exposure, authentication bypasses, or trading-safety vulnerabilities.

Report privately by emailing the maintainer address listed in `pyproject.toml`, or by opening a private GitHub security advisory if available.

Please include:

- affected commit or version,
- reproduction steps,
- expected impact,
- whether credentials, funds, or trading execution may be affected,
- suggested mitigation if known.

## Secrets

Never commit `.env`, API keys, exchange secrets, wallet credentials, or private datasets. Use `.env.example` for documented configuration only.

## Trading Safety

Live trading should require explicit opt-in, testnet validation, configured CORS origins, and successful pretrade checks. Security reports involving unintended live execution are treated as high priority.
