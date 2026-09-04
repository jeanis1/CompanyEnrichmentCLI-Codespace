# CompanyEnrichmentCLI-Codespace

Production-oriented Company Enrichment CLI for a technical AI GTM workflow.

## What it does

- accepts a company domain
- calls an external enrichment API
- handles API/network errors with retries and exponential backoff
- maps provider JSON into a normalized Pydantic `Company`
- calculates an ICP score
- persists results to JSON and CSV
- includes unit and mocked API-client tests

## Architecture

```text
CLI / composition root (main.py)
        |
        v
Company enrichment service ----> CompanyProvider protocol
        |                              ^
        v                              |
Normalized models              AbstractAPIClient
        |
        +----> pure ICP scoring
        |
        +----> persistence adapters (JSON / CSV)
```

The application/service layer depends on a small provider contract instead of importing Abstract API directly. `main.py` wires configuration, the concrete API client, services, and persistence together.

## Responsibilities

- `main.py` - CLI parsing, dependency wiring, user-facing errors
- `config.py` - runtime settings loaded from environment
- `clients/abstract_api.py` - HTTP, retries, provider-specific errors
- `services/company_enrichment.py` - provider-independent enrichment + normalization
- `services/scoring_icp.py` - pure, configurable ICP scoring rules
- `services/persistence.py` - JSON/CSV persistence with injectable output path
- `models/` - normalized Pydantic data contracts
- `tests/` - unit tests and mocked external-boundary tests

## Data flow

```text
domain
  -> CLI
  -> AbstractAPIClient
  -> raw provider JSON
  -> Company enrichment mapper
  -> Pydantic Company
  -> ICP scoring
  -> JSON / CSV
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
ABSTRACT_API_KEY=your_key_here
```

Run:

```bash
python main.py stripe.com
```

Test:

```bash
python -m pytest
```

## Development tasks

1. CLI accepts domain ✅
2. HTTP request works ✅
3. Inspect API JSON ✅
4. Pydantic Company model ✅
5. Convert API response -> Company ✅
6. ICP scoring function ✅
7. Save data to JSON & CSV ✅
8. Handle API/network errors ✅
9. Add retries/backoff ✅
10. Unit tests ✅
11. Mock API tests ✅
12. Clean architecture/refactor ✅
