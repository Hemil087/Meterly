# meterly

You built an API. Someone wants to use it. Now you need to know who's calling it, how often, whether they're abusing it, and how to charge them for it.

That's Meterly.

---

## what it does

Meterly sits between your API and the people calling it. Every request passes through — gets checked, counted, and logged — before it ever reaches your server. Your customers use a Meterly key. They never touch yours.

```
your customer → meterly → your API
```

From the dashboard you can see exactly who's hitting what, who's getting blocked, and who's about to run out of quota.

---

## see it live

```bash
git clone https://github.com/Hemil087/Meterly
cd Meterly

cp .env.example .env
docker compose up -d
alembic upgrade head
```

That's it. Three commands and everything is running — the gateway, the control plane, the database, Redis, and a mock upstream to test against.

Open `localhost:5173` for the dashboard (run `npm install && npm run dev` inside `frontend/` first).

---

## try it

Register a provider and an API through the dashboard, issue an API key, then:

```bash
# Call your API through Meterly
curl -H "X-API-Key: mk_live_your_key_here" \
  http://localhost:8001/yourprovider/yourapi/any/path

# Works with real APIs too — tested with Groq
curl -X POST \
  -H "X-API-Key: mk_live_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"hello"}]}' \
  http://localhost:8001/yourprovider/groq/openai/v1/chat/completions
```

Meterly injects your upstream API key automatically. Your customers never see it.

---

## the dashboard

Five pages — all pulling live data from your own database.

**Overview** — total calls, success rate, average latency, per-consumer breakdown.

**Consumers** — click any consumer to see their hourly traffic chart and current plan. Change their plan from the same screen.

**Events** — a live feed of every request. Outcome, latency, status code, path.

**APIs** — register new APIs, manage plans, set your upstream API key.

**Keys** — issue and revoke API keys. The raw key is shown exactly once.

---

## what gets enforced on every request

In order, before your API ever sees the request:

- Is this key valid and active?
- Is the consumer subscribed to this API?
- Have they hit their per-minute rate limit?
- Have they used up their monthly quota?

If any check fails, the request is blocked and logged. If all pass, it's forwarded and logged.

---

## ports

| Thing | Where |
|---|---|
| Dashboard | `localhost:5173` |
| Gateway (requests go here) | `localhost:8001` |
| Control plane API | `localhost:8080` |
| Swagger docs | `localhost:8080/docs` |

---

## stack

Python · FastAPI · PostgreSQL · Redis · React · Vite · Docker

---

*Built by Hemil Patel*