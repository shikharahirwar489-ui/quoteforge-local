# QuoteForge

**A private, local-first proposal and quote builder for freelancers.** Describe a client's project, enter your rate and estimated hours, and get a proposal draft from the open-weight `llama3.2` model through Ollama. The price is calculated in ordinary code, so the model cannot change the arithmetic.

Built for the Hacktoberfest Open-Source AI Challenge: Week 2 — **Side Hustle**.

## Run it

Requirements: Docker Desktop with Compose and enough disk space for the Ollama image and model. The first launch downloads `llama3.2`; later launches reuse the local model volume.

```sh
docker compose up --build
```

When the model download completes, open [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop with `Ctrl+C`. The app binds to loopback, and the brief is sent only to the local Ollama container. No API key or hosted AI account is used.

## What it does

- Drafts a client proposal from the brief, service, hourly rate, hours, and additional expenses.
- Calculates the estimate deterministically as `rate × hours + expenses` and displays it separately.
- Prompts the model to avoid invented credentials, deliverables, dates, and guarantees, and to mark missing details for confirmation.
- Keeps the generated text in the browser until the user copies it. There is no database, account, analytics, or send-to-client action.
- Runs the UI, API adapter, and model locally using Python's standard library and Ollama.

## Design choices and limits

QuoteForge narrows the AI task to proposal wording. It does not decide whether a quote is profitable, create binding contract language, or send a proposal. Model output can still be inaccurate; review it before sharing. The starter setup uses `llama3.2`, but you can change `OLLAMA_MODEL` to another model available through Ollama.

The browser app has no third-party font, analytics, or AI API requests. The first Docker Compose startup does contact Docker Hub and Ollama's model registry to download the runtime and model; the brief is sent only to the local Ollama service.

## Stack

- Python 3.12 standard library (`http.server`, `urllib`)
- HTML, CSS, and browser JavaScript
- Ollama with the open-weight `llama3.2` model
- Docker Compose

## License

MIT. See [LICENSE](LICENSE).
