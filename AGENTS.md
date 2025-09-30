# AGENTS.md

> **Purpose:** This file tells a coding agent (e.g., ChatGPT Codex – research preview) how to understand, build, test, and safely modify this repository. It explains the architecture, where things live, how to run checks, and what “done” means for common tasks.

---

## 0) Project in one paragraph

**BetterMeals Agents** is a WhatsApp-first, **LangGraph** multi-agent system. A **Supervisor** routes messages to worker agents (Onboarding, Meal Recommender, Meal Scoring, Order, Cook Update). **All domain logic happens via HTTP tools** calling `api.bettermeals.in` (we have mocks for tests). The system uses **durable execution** (checkpoints) and **human-in-the-loop** interrupts (plan, substitution, checkout approvals).

---

## 1) Repo map (important directories & files)

```
src/bettermeals/
  config/
    settings.py              # env config (BM_API_BASE, GROQ_API_KEY, etc.)
    logging.yaml             # console logging
  entrypoints/
    fastapi_app.py           # ASGI app + logging bootstrap
    routes/whatsapp.py       # webhook: JSON → graph ainvoke → JSON reply
  graph/
    state.py                 # TypedDict state shape
    persistence.py           # checkpointer factory (dev: in-memory)
    build.py                 # builds & compiles the graph
    supervisor.py            # (may be present) custom supervisor wiring (Option B)
    workers.py               # worker agents (create_react_agent) + tools
    prompts/                 # prompt files for supervisor/workers
  tools/
    http_client.py           # async http helpers with retries
    onboarding.py            # @tool wrappers → /onboarding/*
    meals.py                 # @tool wrappers → /meals/*
    orders.py                # @tool wrappers → /orders/*
  llms/
    groq.py                  # ChatGroq factories (router/worker models)
  telemetry/
    tracing.py, metrics.py   # stubs for observability
  utils/
    whatsapp_io.py           # tiny mapping helpers

entrypoints are thin; the graph contains business flow. Tools are the only place that talk to external APIs.
```

---

## 2) How to build & run (for the agent)

> The agent runs in an isolated sandbox. Prefer **the simplest path**.

* **Python**: 3.11+
* **Install**: `pip install -r requirements.txt`
* **Run tests**: `pytest -q`
* **Run app (smoke)**: `uvicorn src.bettermeals.entrypoints.fastapi_app:app --port 8000`

### Environment variables

* `GROQ_API_KEY` — required if real ChatGroq is used.
* `BM_API_BASE` — defaults to `https://api.bettermeals.in`.
* For tests, **tools are mocked**, so real network is not required.

> If the sandbox has no internet/keys, **monkeypatch** `ChatGroq` (in `llms/groq.py`) to a no-op echo model for tests/smoke.

---

## 3) Tests you can run (and what they prove)

* `tests/test_tools_*.py` — tool wrappers form correct HTTP calls; mocked responses return expected shapes.
* `tests/test_graph_build.py` — graph compiles.
* `tests/test_supervisor_routing.py` — given an input, routing delegates to the right worker (workers monkeypatched to dummy responders).
* `tests/test_e2e_happy_path.py` — end-to-end **plan → approve → substitute → approve → checkout**, all tools mocked.
* `tests/test_resume_after_restart.py` — durable execution: checkpoint resume works across runs.

> If any of these are missing, please **add** them. Keep external calls mocked.

---

## 4) Running the local webhook (optional)

* After `uvicorn` starts, POST to `/webhooks/whatsapp` with JSON:

  ```json
  { "thread_id": "HH1", "sender_role": "user", "text": "Plan my meals for next week" }
  ```
* Keep the **same `thread_id`** across subsequent requests (“Approved”, “Pick kale”, “Yes”) to test interrupts/resume.

> A ready Postman collection may live under `postman/collection.json`; if missing, add one.

---

## 5) Architecture decisions (what to respect)

* **Supervisor pattern**: One agent at a time; control returns to Supervisor; finish when goal met.
* **API-first**: Never invent meals/scores/orders. Workers must call tools to get facts.
* **Durable execution**: Use the checkpointer; approval steps are **interrupts**; resume by sending the next message for the same `thread_id`.
* **Short replies**: keep WhatsApp responses concise and clear.

---

## 6) Two wiring options (choose one, consistently)

We support two ways to wire the supervisor + workers:

### Option A — **Prebuilt Supervisor** (preferred for simplicity)

* Use `create_supervisor([...])` (from `langgraph_supervisor` package) with compiled worker agents.
* You **do not** pass compiled graphs as tools; you hand the list of worker agents to the factory.
* `build.py` returns `workflow.compile(checkpointer=...)`.

### Option B — **Custom Graph + Handoff Tools** (more control)

* Keep your own `StateGraph`; add nodes manually.
* Supervisor is a `create_react_agent` whose `tools=[...]` are **handoff tools**, created with `create_handoff_tool(agent_name="...")`.
* Node names in the graph **must match** the handoff `agent_name`.

> If the code mixes compiled agents in `tools=[...]`, fix it: use one option consistently. For hackathon speed, pick **Option A**.

---

## 7) Common tasks for the agent (and acceptance criteria)

### T1) **Switch to Option A** (if not already)

* Replace custom supervisor wiring with:

  * `workflow = create_supervisor([onboarding, recommender, scorer, order_agent, cook_update], model=supervisor_llm(), prompt=PROMPT)`
  * `return workflow.compile(checkpointer=...)`
* Remove/retire `graph/supervisor.py` if unused.
* **All tests pass**. Boot `uvicorn` without “CompiledStateGraph passed as tool” errors.

### T2) **Add Postman collection**

* Create `postman/collection.json` with 4 requests:

  * Plan, Approve, Pick substitution, Approve checkout
* Use body shape expected by `/webhooks/whatsapp`.
* Include a small “tests” script ensuring HTTP 200 and a `reply` field.

### T3) **Per-thread lock + deduper**

* Add a tiny in-memory lock keyed by `thread_id` to serialize concurrent invocations.
* Add a request hash or `message_id` kv to drop duplicates in `routes/whatsapp.py`.
* Provide tests that simulate two near-simultaneous messages for the same thread.

### T4) **State reducers**

* Ensure `messages` history is bounded (e.g., keep last 8 turns + rolling summary).
* Provide a reducer or pruning step; add a test asserting the limit.

### T5) **Checkout idempotency**

* In `orders.py`, surface an `idempotency_key` param on `bm_checkout`.
* In E2E tests, simulate retry and assert no duplicate checkout is attempted (mock returns same `order_id`).

---

## 8) Coding & prompt conventions

* **Determinism**: `temperature=0` for Supervisor & workers.
* **Prompts** must include: “Use tools; do not invent domain data. Keep responses brief.”
* **HTTP tools**: must have docstrings and strong type hints for parameters/returns.
* **No secrets in state**: tokens live in env/config; state stores only non-sensitive facts and artifact links (not blobs).

---

## 9) Error handling & messaging rules

* Tool failures → return concise apology in reply **and** set `last_error` in state.
* For human approvals, set `pending_action` to one of:

  * `approve_plan`, `approve_substitution`, `approve_checkout`
* The webhook should reflect `reply` and may include `pending_action` in the JSON for UI layers.

---

## 10) Performance expectations

* Router (Supervisor): larger OSS model (e.g., Llama-3.1-70B or gpt-oss-120b) for fewer misroutes.
* Workers: faster model (e.g., Mixtral-8x7B or gpt-oss-20b).
* Keep prompts short; prune `messages`.
* Avoid extra “glue” nodes that add super-steps without value.

---

## 11) What NOT to change

* Don’t move business logic into LLM prompts: all facts come from tools.
* Don’t store large artifacts in state (store URLs instead).
* Don’t alter public webhook shape without updating Postman + tests.

---

## 12) Deliverables checklist (for any PR you open)

* [ ] All tests green (`pytest -q`).
* [ ] `uvicorn ...fastapi_app:app` boots cleanly.
* [ ] Postman collection present/updated (if the webhook shape changed).
* [ ] README/this AGENTS.md updated if you changed wiring (Option A/B) or flow semantics.
* [ ] Diffs are minimal, commented where non-obvious.

---

## 13) Troubleshooting (quick references)

* **Boot error: “CompiledStateGraph passed as tool”**
  ⇒ You passed a compiled agent graph into Supervisor `tools=[...]`.
  **Fix**: Use Option A (`create_supervisor([...])`) or Option B with `create_handoff_tool(...)`.

* **Approvals don’t advance**
  ⇒ Check you’re reusing the same `thread_id`. Ensure checkpointer is plugged and `pending_action` clears on next message.

* **Model/keys missing in sandbox**
  ⇒ Monkeypatch `ChatGroq` in `llms/groq.py` to return a dummy echo model for tests.

* **State blow-up**
  ⇒ Add/prune reducers for `messages`. Store artifacts as URLs only.

* **Races / duplicate actions**
  ⇒ Add per-thread locks & webhook dedupe. Ensure checkout uses `idempotency_key`.

---

*Thanks for helping! Keep changes focused, reviewed, and well-tested. If something is ambiguous, prefer Option A wiring and small PRs with strong tests.*
