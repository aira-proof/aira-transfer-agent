# Aira Transfer Agent

A fully governed wire transfer agent powered by [Aira](https://airaproof.com). Every transfer is authorized before execution, notarized after, and produces a cryptographic receipt any regulator can independently verify.

## What this demonstrates

- **Pre-execution authorization** — the agent calls `aira.authorize()` before moving money
- **Cryptographic receipts** — every decision is signed with Ed25519 and timestamped with RFC 3161
- **Policy enforcement** — set up rules to deny, approve, or escalate transfers based on amount, country, or content
- **Public verification** — each receipt has a URL anyone can verify without an account

## Quick start

```bash
# Clone
git clone https://github.com/aira-proof/aira-transfer-agent.git
cd aira-transfer-agent

# Set your API key (get one free at https://airaproof.com/register)
cp .env.example .env
# Edit .env and add your AIRA_API_KEY

# Run with Docker
docker compose up --build

# Or run directly
pip install -r requirements.txt
uvicorn app.main:app --port 8080
```

Open [http://localhost:8080](http://localhost:8080) and try the preset scenarios.

## Preset scenarios

| Preset | Amount | What happens |
|--------|--------|-------------|
| Small (€500) | €500 | Authorized and executed — low-risk, within policy |
| Medium (€25K) | €25,000 | Authorized — passes threshold checks |
| Large (€250K) | €250,000 | May trigger escalation — high-value human approval |
| Sanctioned country | €8,500 to RU | Denied — sanctioned country policy violation |

## How it works

```
User submits transfer
        │
        ▼
  ┌─────────────┐
  │ Agent calls  │
  │ authorize()  │──── Aira checks policies
  └──────┬──────┘     (rules, AI, content scan)
         │
    ┌────┴────┐
    │         │
 Approved   Denied/Escalated
    │         │
    ▼         ▼
 Execute    Return denial
 transfer   with receipt
    │
    ▼
 notarize()
 (Ed25519 receipt)
    │
    ▼
 Verify URL:
 airaproof.com/verify/{uuid}
```

## Project structure

```
├── app/
│   ├── main.py       # FastAPI routes + static file serving
│   ├── agent.py      # Transfer agent with Aira governance
│   └── models.py     # Pydantic models
├── static/
│   └── index.html    # Single-page dashboard
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Setting up policies

Create policies in your [Aira dashboard](https://airaproof.com/dashboard/settings/policies) or via the SDK:

```python
from aira import Aira

aira = Aira(api_key="aira_live_xxx")

# Block transfers to sanctioned countries
aira.create_policy(
    name="sanctioned-countries",
    mode="rules",
    decision="deny",
    priority=100,
    conditions={"country": {"in": ["RU", "KP", "IR", "SY", "CU"]}},
    description="Block wire transfers to OFAC/EU sanctioned jurisdictions",
)

# Require human approval for large transfers
aira.create_policy(
    name="large-transfer-approval",
    mode="rules",
    decision="escalate",
    priority=50,
    conditions={"amount_eur": {"gte": 100000}},
    description="Escalate transfers >= €100K for human approval",
)
```

## License

MIT

## Links

- [Aira](https://airaproof.com) — Authorization & audit for AI agents
- [Documentation](https://docs.airaproof.com)
- [Python SDK](https://pypi.org/project/aira-sdk/)
- [Blog: Agentic Payments Need Audit Trails](https://airaproof.com/blog/agentic-payments-audit-trail)
