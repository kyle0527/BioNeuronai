# Contributing

Thanks for helping improve BioNeuronAI. This project touches trading, ML, and deployment code, so changes should be reproducible and conservative.

## Local Setup

```bash
cp .env.example .env
docker compose up api
```

## Operational Validation

```bash
curl http://localhost:8000/api/v1/status
docker compose ps
```

The primary validation path is direct operation through Docker and real API endpoints. If you change trading flows, include the exact CLI, API, or dashboard operation you used to verify the behavior.

## Pull Request Standard

- Explain the behavior change and why it is needed.
- Include operational evidence or explain why direct validation was not possible.
- Do not publish performance claims without reproducible artifacts.
- Keep generated assets under `docs/assets/` and document how they were produced.
- Avoid committing secrets, `.env`, exchange keys, private datasets, or large raw outputs.

## Performance Claims

Use `docs/assets/performance_artifacts.md` for backtest and latency evidence. README should only include numbers that can be reproduced from documented commands and committed artifacts.
