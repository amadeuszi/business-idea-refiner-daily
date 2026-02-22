# Idea Refiner

**Automatic business idea inspiration sent to you daily via Telegram bot.**

Idea Refiner is an agentic AI pipeline that generates micro-SaaS and micro-product business ideas using multiple AI models, pits them against a ruthless AI judge, and iterates with targeted feedback until it finds something genuinely worth building — or gives you the best of what it found.

It implements the [Evaluator-Optimizer](https://www.anthropic.com/research/building-effective-agents#workflow-evaluator-optimizer) agentic pattern: generators propose ideas in parallel, an LLM judge scores and critiques them, and the feedback loop drives each subsequent round closer to a viable idea.

## How it works

```mermaid
flowchart LR
    subgraph Round1 [Round 1]
        G1[GPT-5.2] --> J1{Judge Gemini}
        GM1[Gemini] --> J1
    end

    subgraph RoundN [Round N]
        GN[GPT-5.2] --> JN{Judge Gemini}
        GMN[Gemini] --> JN
    end

    J1 -- "✗ reject + feedback" --> RoundN
    JN -- "✓ accept!" --> Ship["Telegram / Console"]
```

1. **Generate** — Two AI models (GPT-5.2 and Gemini) independently brainstorm ideas in parallel, each with a structured format covering product name, pricing, ad strategy, and a concrete 2-week build plan.

2. **Judge** — A separate AI judge scores each idea on three criteria: ease of customer acquisition, market demand, and build simplicity. The bar is high — all three scores must be 9+ out of 10.

3. **Iterate** — If no idea passes, the judge provides specific feedback ("the ad hook is unclear", "chicken-and-egg problem") and both generators try again with that feedback baked in.

4. **Ship** — When an idea passes the quality gate (or after max retries), the winner is displayed and optionally pushed to Telegram.

## What kind of ideas?

Ideas optimized for solo developers who want:
- An MVP buildable in **1-2 weeks**
- **Subscription pricing** ($1-29/month) — recurring revenue
- Customers acquirable through **paid ads** (Facebook, Instagram, Google)
- A clear **path to $100/month** with simple math
- Something that's genuinely **fun to build and run**

Every other run focuses on a random theme from a pool of 100+ niches — everything from "pet owners" to "Etsy sellers" to "procrastination" to "meal preppers".

## Quick start

```bash
# Clone and setup
git clone <repo-url> && cd amadeusz_agents
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure API keys
cp .env.example .env
# Edit .env with your OpenAI and Google API keys

# Generate ideas
python -m agents.idea_refiner
```

Or use the CLI shortcut (after install):

```bash
idea-refiner
```

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key (for GPT-5.2) |
| `GOOGLE_API_KEY` | Yes | Google API key (for Gemini via OpenAI-compatible endpoint) |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token for push notifications |
| `TELEGRAM_CHAT_ID` | No | Telegram chat ID to receive ideas |

## Deploy to Google Cloud Run Functions

### Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A GCP project with the **Cloud Functions** and **Cloud Build** APIs enabled
- API keys stored in [Secret Manager](https://cloud.google.com/secret-manager) (recommended)

### Store secrets

```bash
echo -n "sk-..." | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "AI..." | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Optional — for Telegram notifications
echo -n "123456:ABC..." | gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=-
echo -n "987654321"     | gcloud secrets create TELEGRAM_CHAT_ID --data-file=-
```

### Deploy

```bash
gcloud functions deploy idea-refiner \
  --gen2 \
  --runtime python313 \
  --trigger-http \
  --entry-point idea_refiner \
  --region us-central1 \
  --timeout 300 \
  --memory 512Mi \
  --set-secrets 'OPENAI_API_KEY=OPENAI_API_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest' \
  --allow-unauthenticated
```

> Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to `--set-secrets` if you want
> Telegram notifications. Remove `--allow-unauthenticated` if the function should
> require IAM authentication.

### Invoke

```bash
curl https://REGION-PROJECT_ID.cloudfunctions.net/idea-refiner
```

### Run locally

```bash
uv sync --dev
functions-framework --target idea_refiner --debug
```

### Schedule daily runs (optional)

Use [Cloud Scheduler](https://cloud.google.com/scheduler) to trigger the function on a cron schedule:

```bash
gcloud scheduler jobs create http idea-refiner-daily \
  --schedule "0 8 * * *" \
  --uri "https://REGION-PROJECT_ID.cloudfunctions.net/idea-refiner" \
  --http-method POST \
  --time-zone "UTC"
```

## Project structure

```
main.py                          # Cloud Run Function entry point
requirements.txt                 # Dependencies for Cloud Run Functions deploy
src/agents/idea_refiner/
├── main.py                  # CLI entry point — runs the pipeline
├── config.py                # Prompts, themes, and settings
├── generation/
│   ├── runner.py            # Parallel async idea generation
│   ├── gpt52.py             # GPT-5.2 wrapper
│   ├── gemini.py            # Gemini wrapper
│   ├── clients.py           # API client factory
│   ├── models.py            # Model registry
│   └── prompt.py            # Prompt builder
├── judging/
│   ├── judge.py             # AI judge with label shuffling
│   └── quality_gate.py      # Score threshold enforcement
├── pipeline/
│   ├── run_round.py         # Generate → judge → verdict loop
│   ├── generate_step.py     # Generation orchestration
│   ├── judge_step.py        # Judging orchestration
│   ├── verdict.py           # Accept/reject routing
│   ├── accept.py            # Winner selection
│   ├── retry.py             # Feedback-driven retry logic
│   └── state.py             # Pipeline state management
└── output/
    ├── display.py           # Output orchestrator
    ├── console.py           # Terminal scoreboard
    └── telegram.py          # Telegram notifications
```

## License

MIT
