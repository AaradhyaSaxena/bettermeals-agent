# AGENTS.md

> **Purpose:** This file tells a coding agent (e.g., ChatGPT Codex – research preview) how to understand, build, test, and safely modify this repository. It explains the architecture, where things live, how to run checks, and what “done” means for common tasks.

---

## 0) Project in one paragraph

**BetterMeals Agents** is a WhatsApp-first, **dual-architecture** multi-agent system. For **users**, a **LangGraph Supervisor** routes messages to worker agents (Onboarding, Meal Recommender, Meal Scoring, Order) for structured workflows. For **cooks**, an **AWS Bedrock/MCP Cook Assistant** provides open-ended conversational support with AgentCore semantic memory. **All domain logic happens via HTTP tools** calling `api.bettermeals.in`. The LangGraph system uses **durable execution** (checkpoints) and **human-in-the-loop** interrupts (plan, substitution, checkout approvals). Cook messages are routed at the webhook layer and bypass LangGraph entirely.

---

## 1) Repo map (important directories & files)

```
src/bettermeals/
  config/
    settings.py              # env config (BM_API_BASE, GROQ_API_KEY, AWS_REGION, etc.)
    logging.yaml             # console logging
  entrypoints/
    fastapi_app.py           # ASGI app + logging bootstrap
    routes/whatsapp.py       # webhook: routes cooks → CookAssistantService, users → LangGraph
  graph/
    state.py                 # TypedDict state shape (LangGraph only)
    persistence.py           # checkpointer factory (dev: in-memory)
    build.py                 # builds & compiles the LangGraph
    supervisor.py            # (may be present) custom supervisor wiring (Option B)
    workers.py               # LangGraph worker agents (create_react_agent) + tools
    prompts/                 # prompt files for supervisor/workers
    cook_assistant/          # AWS Bedrock/MCP Cook Assistant (separate from LangGraph)
      service.py             # CookAssistantService: routes cook messages, builds context
      bedrock_client.py       # Bedrock agent invocation, MCP client, AgentCore memory
      memory_config.py       # AgentCore memory resource management
      utils.py               # AWS SSM parameter helpers, Cognito auth
      .agentcore.json        # AgentCore config file
  tools/
    http_client.py           # async http helpers with retries
    onboarding.py            # @tool wrappers → /onboarding/*
    meals.py                 # @tool wrappers → /meals/*
    orders.py                # @tool wrappers → /orders/*
  llms/
    groq.py                  # ChatGroq factories (router/worker models)
  database/
    database.py              # Firebase client, cook detection, message persistence
  telemetry/
    tracing.py, metrics.py   # stubs for observability
  utils/
    whatsapp_io.py           # tiny mapping helpers

entrypoints are thin; routing happens in routes/whatsapp.py. LangGraph handles user workflows; Cook Assistant handles cook conversations independently.
```

---

## 2) How to build & run (for the agent)

> The agent runs in an isolated sandbox. Prefer **the simplest path**.

* **Python**: 3.11+
* **Install**: `pip install -r requirements.txt`
* **Run tests**: `pytest -q`
* **Run app (smoke)**: `uvicorn src.bettermeals.entrypoints.fastapi_app:app --port 8000`

### Environment variables

* `GROQ_API_KEY` — required if real ChatGroq is used for LangGraph agents.
* `BM_API_BASE` — defaults to `https://api.bettermeals.in`.
* `AWS_REGION` — required for Bedrock/MCP Cook Assistant (defaults to us-east-1 if not set).
* AWS credentials — required for Bedrock/MCP (via boto3: env vars, IAM role, or ~/.aws/credentials).
* SSM parameters — Cook Assistant reads from `/app/cookassistant/agentcore/*` (gateway_url, memory_id, cognito_provider, etc.).
* For tests, **tools are mocked**, so real network is not required.

> If the sandbox has no internet/keys, **monkeypatch** `ChatGroq` (in `llms/groq.py`) to a no-op echo model for tests/smoke. Cook Assistant tests may require AWS credentials/SSM mocks.

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

* After `uvicorn` starts, POST to `/whatsapp` (not `/webhooks/whatsapp`) with JSON:

  ```json
  { "phone_number": "+1234567890", "text": "Plan my meals for next week" }
  ```
* For **cook messages**, use a phone number that exists in Firebase `cooks` collection.
* For **user messages**, keep the **same `phone_number`** across subsequent requests ("Approved", "Pick kale", "Yes") to test interrupts/resume.

> A ready Postman collection may live under `postman/collection.json`; if missing, add one.

---

## 5) Architecture decisions (what to respect)

* **Dual architecture**: Cook messages route to Bedrock/MCP Cook Assistant (bypasses LangGraph). User messages route to LangGraph Supervisor.
* **Supervisor pattern** (LangGraph only): One agent at a time; control returns to Supervisor; finish when goal met.
* **API-first**: Never invent meals/scores/orders. Workers must call tools to get facts.
* **Durable execution** (LangGraph only): Use the checkpointer; approval steps are **interrupts**; resume by sending the next message for the same `phone_number`.
* **Short replies**: keep WhatsApp responses concise and clear.
* **Cook Assistant independence**: Cook Assistant doesn't touch LangGraph state; LangGraph doesn't handle cook conversations.

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

  * `workflow = create_supervisor([onboarding, recommender, scorer, order_agent], model=supervisor_llm(), prompt=PROMPT)`
  * `return workflow.compile(checkpointer=...)`
* Remove/retire `graph/supervisor.py` if unused.
* **All tests pass**. Boot `uvicorn` without "CompiledStateGraph passed as tool" errors.
* **Note**: Cook Assistant is handled separately in `routes/whatsapp.py` and doesn't need to be added to LangGraph workers.

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

* **LangGraph**: Tool failures → return concise apology in reply **and** set `last_error` in state.
* **Cook Assistant**: Errors are caught in `CookAssistantService.process_cook_message()` and return user-friendly error messages. All conversations are persisted to Firebase for audit.
* For human approvals (LangGraph only), set `pending_action` to one of:

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

* **Boot error: "CompiledStateGraph passed as tool"**
  ⇒ You passed a compiled agent graph into Supervisor `tools=[...]`.
  **Fix**: Use Option A (`create_supervisor([...])`) or Option B with `create_handoff_tool(...)`.

* **Cook messages not routing to Cook Assistant**
  ⇒ Check `cook_assistant_service.is_cook(phone_number)` returns `True`. Verify phone number exists in Firebase `cooks` collection. Check webhook route is `/whatsapp` (not `/webhooks/whatsapp`).

* **Cook Assistant Bedrock errors**
  ⇒ Verify AWS credentials are configured. Check SSM parameters exist: `/app/cookassistant/agentcore/gateway_url`, `/app/cookassistant/agentcore/memory_id`, etc. Verify `.agentcore.json` exists in `graph/cook_assistant/`.

* **Approvals don't advance** (LangGraph)
  ⇒ Check you're reusing the same `phone_number`. Ensure checkpointer is plugged and `pending_action` clears on next message.

* **Model/keys missing in sandbox**
  ⇒ Monkeypatch `ChatGroq` in `llms/groq.py` to return a dummy echo model for tests. For Cook Assistant, mock `invoke_cook_assistant` in tests.

* **State blow-up** (LangGraph)
  ⇒ Add/prune reducers for `messages`. Store artifacts as URLs only.

* **Races / duplicate actions**
  ⇒ Add per-thread locks & webhook dedupe. Ensure checkout uses `idempotency_key`.

---

*Thanks for helping! Keep changes focused, reviewed, and well-tested. If something is ambiguous, prefer Option A wiring and small PRs with strong tests.*
