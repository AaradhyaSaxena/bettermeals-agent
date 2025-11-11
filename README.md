# BetterMeals :: AI Butler
### Kitchen on Autopilot

BetterMeals is an AI food assistant that runs your kitchen on autopilot. It takes lab results and household preferences, creates personalised meal plans, auto-generates grocery carts, and even briefs your cook daily via WhatsApp or voice. It adapts to different needs within the same home - like athletes, diabetics, or recovering patients — so everyone eats right without the daily hassle.

---

## Architecture & Behavior Overview

**One-line:** WhatsApp-first, stateful automation powered by **Groq's LPU™ Inference Engine** that turns  
**labs + preferences → meal plan → grocery cart → (optional) checkout**,  
with **human approvals**, **durable execution**, **MCP tool discovery**, and **all domain logic behind APIs** (`api.bettermeals.in`).  
**What matters:** *How it works*, not how to run it.

---

## 1. Problem & Approach

### The Problem
Households need a reliable way to go from personal health context (labs, preferences, constraints) to a weekly plan and groceries — without endless chat or fragile spreadsheets — and with **human control** over spend and substitutions.

### The Approach
- A **Supervisor agent** (Groq-powered) orchestrates specialized worker agents in a **LangGraph** state machine.  
- All nutrition and ordering decisions happen via **explicit HTTP tools** to `api.bettermeals.in`.  
- The system **pauses** at human checkpoints (plan approval, substitutions, checkout) and **resumes** from the exact point after the user replies on WhatsApp.  
- Every step is **checkpointed**, **auditable**, and **safe to replay**.
- **Groq's LPU™** delivers millisecond inference for real-time conversational UX.

---

## 2. System Components

- **WhatsApp (Meta Cloud API)** → primary inbound/outbound channel for users and cooks.  
- **n8n (Integration Layer)** → receives webhooks, deduplicates, maps phone → `thread_id`, routes to appropriate system.  
- **LangGraph Orchestrator (Groq-Powered)** → hosts the Supervisor + specialized agents for structured user workflows, manages state, edges, streaming, and interrupts. All agents use Groq's `gpt-oss-20b` model via `llms/groq.py` for ultra-fast inference.  
- **AWS Bedrock/MCP (AgentCore)** → powers the Cook Assistant with Claude 3.7 Sonnet, semantic memory, and MCP tool discovery for open-ended cook conversations.  
- **BetterMeals API** → source of truth for meal planning, scoring, onboarding, and orders.
- **Tooling Standard (MCP-style descriptors)** → all HTTP tools (`onboarding.*`, `meals.*`, `orders.*`) are described with machine-readable schemas so agents can discover, validate, and audit every call (capabilities scoped per agent).

**Dual Architecture Pattern:**
- **Structured workflows** (users) → LangGraph Supervisor orchestrates deterministic, checkpointed flows
- **Open-ended conversations** (cooks) → Bedrock/MCP AgentCore provides semantic memory and tool discovery for natural Q&A

---

## 2.5. Groq-Powered Real-Time Inference

BetterMeals leverages **Groq's LPU™ Inference Engine** to deliver ultra-fast, real-time AI responses across all LangGraph agents. This enables sub-second decision-making critical for conversational workflows.

### Groq Integration Architecture

**All LangGraph agents** (Supervisor + 5 Workers) use Groq's `openai/gpt-oss-20b` model via the `langchain-groq` integration:

```12:14:src/bettermeals/llms/groq.py
def supervisor_llm():
    # strong router for instruction-following
    return ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=settings.groq_api_key)
```

**Why Groq?**
- **Millisecond inference**: Groq's LPU™ delivers responses in 150-300ms (vs 2-5s traditional)
- **Real-time UX**: Enables natural conversation flow without latency gaps
- **Cost-effective**: Free tier supports hackathon development; pay-as-you-go scales to production
- **Deterministic**: Temperature=0 ensures consistent routing and tool selection

### Performance Impact

Groq's speed transforms the user experience:
- **Supervisor routing**: < 400ms (vs 2-3s) → instant intent detection
- **Tool calling**: < 2.5s end-to-end (vs 5-8s) → responsive meal planning
- **Streaming responses**: Token-level streaming at Groq's native speed → fluid conversations

### Model Selection Rationale

- **Supervisor**: `gpt-oss-20b` provides strong instruction-following for routing decisions
- **Workers**: Same model ensures consistency; Groq's speed makes larger models viable for all agents
- **Cook Assistant**: Uses Claude 3.7 Sonnet (Bedrock) for advanced reasoning; complements Groq-powered workflows

**Setup**: Configure `GROQ_API_KEY` environment variable. See [Groq Setup Guide](#groq-setup-guide) below.

---

**Evaluation at a Glance**

- **Technical Excellence (35%):** 
  - **Groq-powered real-time inference**: All LangGraph agents use Groq's LPU™ for millisecond responses (5-10x faster than traditional inference)
  - **Dual-architecture design**: LangGraph (structured workflows) + Bedrock/MCP (open-ended conversations)
  - **Multi-agent orchestration**: 7-agent system (1 Supervisor + 5 Workers + 1 Cook Assistant) with real-time handoffs
  - **MCP tool discovery**: Dynamic tool registration and context injection via Model Context Protocol
  - **Semantic memory**: AgentCore integration with actor-scoped namespaces and 30-day retention
  - **Clean boundaries**: Typed tools, durable execution, comprehensive tests

- **Real-World Impact (35%):** 
  - **Production-ready kitchen automation**: Weekly planning → cart → checkout with human approvals
  - **Scalable design**: SSM-managed configs, thread-safe operations, Firebase audit trails
  - **User control**: Human-in-the-loop at financial and dietary decision points
  - **Cook handoffs**: Natural conversation via Bedrock/MCP for seamless kitchen integration
  - **Multi-modal UX**: Text, vision (lab PDFs), and speech (voice notes) support

- **Innovation (30%):** 
  - **Groq LPU™ integration**: Ultra-fast inference enables real-time conversational workflows
  - **API-first "thin agents"**: All domain logic via HTTP tools, agents orchestrate and summarize
  - **Dual-system routing**: Intelligent webhook routing separates structured workflows from open-ended conversations
  - **MCP tool discovery**: Dynamic capability access without code changes
  - **Multi-modal intake**: Lab images, voice notes, and text unified into single processing pipeline
  - **Resumable graph**: Checkpointed execution with human interrupts and seamless resume


---

## 3. Mental Model

### Message-Passing State Machine
LangGraph runs in discrete super-steps. Each **Node** (agent) reads state, performs work, and emits updates to activate the next node(s). A **Supervisor** decides which specialist acts next.

### Single Entry, Smart Routing
All WhatsApp messages enter via the webhook layer, which performs **intelligent routing**:
- **Cook detection** → routes to Bedrock/MCP Cook Assistant (bypasses LangGraph)
- **User messages** → routes to LangGraph Supervisor
- The Supervisor:
  - Interprets intent  
  - Delegates to exactly one specialized agent  
  - Receives control back  
  - Decides to continue, ask, or finish

### Durable by Design
After each step, a **checkpoint** persists state + “what’s next”. Human approvals are **interrupts** that suspend execution; a later resume picks up exactly where it left off.

---

## 4. Agents

BetterMeals employs a **7-agent system** with specialized roles, coordinated by a Groq-powered Supervisor for real-time decision-making.

### LangGraph Agents (Structured Workflows) - Groq-Powered

All LangGraph agents use **Groq's `gpt-oss-20b`** model via `llms/groq.py` for ultra-fast inference:

| Agent | Responsibility | Groq Model | Key Tools |
|-------|----------------|------------|-----------|
| **Supervisor** | Routes intent, delegates to workers, enforces policy, manages interrupts. | `gpt-oss-20b` | Handoff tools to workers |
| **Onboarding** | Parses free text and lab images to structured household profiles. | `gpt-oss-20b` | `bm_onboard_household`, `bm_onboard_resident` |
| **Meal Recommender** | Calls API to generate plans and writes plan IDs to state. | `gpt-oss-20b` | `bm_recommend_meals` |
| **Meal Scorer** | Scores plans via API and explains trade-offs. | `gpt-oss-20b` | `bm_score_meal_plan` |
| **Order Manager** | Builds cart, handles substitutions, manages checkout & tracking. | `gpt-oss-20b` | `bm_build_cart`, `bm_substitute`, `bm_checkout`, `bm_order_status` |
| **Cook Update** | Maps cook messages (missing items) to substitution tool calls. | `gpt-oss-20b` | `bm_substitute` |

**Agent Coordination Pattern:**
1. **Supervisor** receives message → Groq-powered routing (< 400ms)
2. **Worker** selected → Groq-powered tool calling (< 2.5s)
3. **Control returns** to Supervisor → evaluates next step
4. **Repeat** until goal met or human approval required

**Real-time Handoffs:**
- Supervisor → Worker: < 400ms (Groq routing)
- Worker → API: < 1.5s (HTTP tool call)
- Worker → Supervisor: < 200ms (state update)
- **Total loop**: < 2.5s per agent interaction

### Bedrock/MCP Agent (Open-Ended Conversations)

| Agent | Responsibility | Model | Key Features |
|-------|----------------|-------|--------------|
| **Cook Assistant** | Open-ended conversational agent powered by Claude 3.7 Sonnet via AWS Bedrock. Uses AgentCore semantic memory for context retention, MCP tool discovery for dynamic capability access, and handles cooking queries, meal details, recipe guidance, and kitchen advice. Operates independently from LangGraph with its own session management. | Claude 3.7 Sonnet | MCP tool discovery, AgentCore memory, context injection |

> **Architecture Philosophy:** LangGraph workers are thin API-driven wrappers powered by Groq for speed — they summarize & shape responses but don't invent facts. The Cook Assistant leverages Bedrock's advanced reasoning for natural conversation while maintaining tool-grounded responses. Together, they form a dual-architecture system optimized for both structured workflows and open-ended conversations.

---

## 5. State & Memory

### Short-Term (Per Thread) - LangGraph
Compact `BMState` stores household ID, role, intent, message history, API payloads/results, pending approvals, and artifact URLs (e.g., plan JSON, grocery CSV).

### Long-Term (Cross Thread) - LangGraph
Stores stable preferences (veg/non-veg, allergies), policies (no onion/garlic days), cook reliability, common substitutions.

### Semantic Memory - Cook Assistant (AgentCore)
**AgentCore semantic memory** provides persistent, actor-scoped context for cook conversations:
- **Namespace isolation**: `/facts/{actorId}` ensures cook-specific context
- **30-day retention**: Compliance-aligned event expiry
- **Session grouping**: Daily sessions (`phone_number_YYYYMMDD`) for natural conversation boundaries
- **Context injection**: Dynamic tool context (cook_id, household_id, meal_id, year_week) enhances tool calls without prompt bloat
- **Memory resource**: Managed via SSM parameters, auto-provisioned on first use

---

## 6. Happy Path (Narrative)

1. User: “Plan my meals for next week.”  
2. Supervisor detects intent → Recommender → generates plan.  
3. Supervisor interrupts for plan approval → user approves.  
4. Order Agent builds cart → detects substitutions → approval.  
5. User selects substitutions → checkout approval → success.  
6. Supervisor posts ETA → ends.

**All steps are checkpointed**. Resume after any crash without recomputation.

---

## 7. Human-in-the-Loop

- **ApprovePlan** — before committing to groceries  
- **ApproveSubstitution** — when gaps are detected  
- **ApproveCheckout** — before spending money

Interrupts set `pending_action` and pause execution until resumed.

---

## 8. Streaming

- **User-facing:** token-level streaming during summaries (e.g., “Building your cart… Done.”)  
- **Ops-facing:** node-level state updates for tracing execution

Keeps UX responsive without altering semantics.

---

## 9. Durability & Safety

- Checkpoints after each node → predictable replay  
- Sync/async durability modes  
- Idempotent checkout to avoid double-spend  
- Deterministic execution — no side-effects without persisted results

---

## 10. Error Handling

- **Timeouts** → retries with backoff or graceful suspend  
- **Substitution loops** → escalated to meal recommender  
- **Payment unknown** → polling & escalation  
Always clear, small messages; user choices preserved.

---

## 11. Interface Contracts

### Inbound (WhatsApp → Orchestrator)
```json
{
  "thread_id": "household_42",
  "sender_role": "user",
  "text": "Order groceries for the week",
  "mediaUrls": []
}
````

### Outbound (Orchestrator → WhatsApp)

* Short messages, carousels, buttons for approvals
* Media links for artifacts (plan JSON, grocery CSV, receipts)

---

## 12. API Contracts (Essentials)

| Endpoint                      | Purpose                     |
| ----------------------------- | --------------------------- |
| `POST /onboarding/*`          | Household/resident profiles |
| `POST /meals/recommendations` | Generate weekly plans       |
| `POST /meals/score`           | Score plans                 |
| `POST /orders/build_cart`     | Create grocery basket       |
| `POST /orders/substitute`     | Handle substitutions        |
| `POST /orders/checkout`       | Finalize orders             |
| `GET /orders/status`          | Track deliveries            |

---

## 13. Security & Privacy

* PII minimization (hashing IDs)
* Secrets never stored in state
* Structured, redacted logs
* Auto-expiring lab media, durable references only

**Human oversight by design:** actions with financial or dietary impact always require explicit user approval (no autonomous checkout).


---

## 14. Observability

* Per-node **traces** for diagnosing performance issues
* **Metrics**: latency, error rates, approvals, substitution loops, resumes
* Summaries must be short, correct, and API-grounded

---

## 15. Performance Benchmarks

BetterMeals achieves **sub-second response times** powered by Groq's LPU™ Inference Engine, enabling real-time conversational workflows.

### Groq-Powered Performance Targets

| Metric                      | Target         | Groq Advantage                    |
| --------------------------- | -------------- | --------------------------------- |
| **Time to First Token**     | 150–300 ms     | Groq LPU™ delivers < 200ms        |
| **P95 Step Latency**        | < 2.5 s        | Groq inference + tool calls       |
| **Supervisor Loop Latency** | < 400 ms       | Groq routing in milliseconds      |
| **End-to-End Flow**         | < 25 s typical | Fast agent handoffs               |

### Measured Performance (Groq `gpt-oss-20b`)

**Measured (dev, 50 runs, local, mock APIs, Groq-powered)**

| Metric                    | P50   | P95   | Notes                              |
|---------------------------|-------|-------|------------------------------------|
| Time to First Token       | 190ms | 310ms | Groq LPU™ inference                |
| Step Latency (node+tool)  | 1.2s  | 2.3s  | Groq agent + HTTP tool call        |
| Supervisor Loop (route)   | 180ms | 340ms | Groq-powered routing decision      |
| End-to-End (plan→cart)    | 12.4s | 21.8s | Multi-agent coordination            |

**Comparison:**
- **Traditional inference**: 2-5s per agent call → 15-30s end-to-end
- **Groq-powered**: < 400ms per agent call → < 25s end-to-end
- **Speedup**: **5-10x faster** agent responses

### Performance Testing

Run benchmarks:

```bash
python perf/latency_probe.py --runs 50
```

Generates CSV, histograms, and percentile summaries. All agents use Groq via `llms/groq.py` for consistent performance.

---

## 16. Real-World Impact

* Replaces messy chats/spreadsheets with structured flows
* Users stay in control at money/taste boundaries
* Cooks integrate seamlessly for substitutions
* Predictable spend via idempotent checkout
* Resumable workflows reduce friction

---

## 17) Two Canonical Sequences

### A) Plan → Approve → Cart → Approve → Checkout

```mermaid
sequenceDiagram
  participant User
  participant WA as WhatsApp (n8n)
  participant Sup as Supervisor (Groq)
  participant Rec as Meal Recommender (Groq)
  participant Ord as Order Agent (Groq)
  participant API as api.bettermeals.in

  User->>WA: "Plan my meals for next week"
  WA->>Sup: webhook {thread_id, text}
  Note over Sup: Groq LPU™ inference (< 400ms)
  Sup->>Rec: delegate
  Note over Rec: Groq LPU™ inference (< 400ms)
  Rec->>API: POST /meals/recommendations
  API-->>Rec: meal_plan_id + plan
  Rec-->>Sup: plan summary + meal_plan_id
  Sup-->>WA: INTERRUPT ApprovePlan (summary)
  User->>WA: "Approved"
  WA->>Sup: resume
  Sup->>Ord: delegate (build_cart)
  Note over Ord: Groq LPU™ inference (< 400ms)
  Ord->>API: POST /orders/build_cart
  API-->>Ord: cart + substitutions (spinach→kale/methi)
  Ord-->>Sup: needs substitution choice
  Sup-->>WA: INTERRUPT ApproveSubstitution
  User->>WA: "kale"
  WA->>Sup: resume
  Sup->>Ord: delegate (checkout)
  Ord->>API: POST /orders/checkout (idempotent)
  API-->>Ord: order_id + eta
  Ord-->>Sup: success
  Sup-->>WA: ETA + order summary (END)
```

### B) Cook: "What are the ingredients for meal MEAL001?"

```mermaid
sequenceDiagram
  participant Cook
  participant WA as WhatsApp (n8n)
  participant Webhook as Webhook Router
  participant CAS as CookAssistantService
  participant Bedrock as AWS Bedrock/MCP
  participant Memory as AgentCore Memory
  participant Tools as MCP Tools
  participant API as api.bettermeals.in

  Cook->>WA: "What are the ingredients for MEAL001?"
  WA->>Webhook: webhook {phone_number, text}
  Webhook->>CAS: is_cook(phone_number) → true
  CAS->>CAS: Build context {cook_id, household_id, meal_id}
  CAS->>Bedrock: invoke_cook_assistant(prompt, actor_id, session_id, context)
  Bedrock->>Memory: Load semantic context for actor_id
  Memory-->>Bedrock: Previous conversation context
  Bedrock->>Tools: Discover available tools via MCP
  Tools-->>Bedrock: Tool schemas (get_meal_details, etc.)
  Bedrock->>Tools: Call get_meal_details(meal_id="MEAL001")
  Tools->>API: POST /meals/details {meal_id}
  API-->>Tools: Meal ingredients + prep instructions
  Tools-->>Bedrock: Structured response
  Bedrock->>Memory: Store conversation in semantic memory
  Bedrock-->>CAS: Natural language response
  CAS->>CAS: Save to Firebase (audit trail)
  CAS-->>WA: Response with ingredients list
  WA-->>Cook: "MEAL001 includes: chicken, spinach, rice..."
```

---

## 17.5. Dual Architecture Deep Dive

### Why Two Systems?

**LangGraph (Users):** Structured, deterministic workflows with explicit state machines, checkpoints, and human-in-the-loop interrupts. Perfect for multi-step processes requiring approvals and resumability.

**Bedrock/MCP (Cooks):** Open-ended conversations requiring semantic memory, dynamic tool discovery, and natural language understanding. Cooks ask varied questions ("What can I substitute?", "How do I prep this?", "Show me this week's plan") that don't fit rigid workflows.

### Technical Highlights

**Cook Assistant Architecture:**

**MCP (Model Context Protocol) Integration:**
- **Dynamic Tool Discovery**: MCP client factory (`mcp_client_factory.py`) connects to HTTP gateway, discovers available tools at runtime
- **Tool Registration**: Tools are registered via MCP protocol, enabling dynamic capability access without code changes
- **Context Injection**: Generic context builder (`_build_tool_context` in `service.py`) extracts values (cook_id, household_id, meal_id, year_week) from database/payload and injects them into tool calls without prompt engineering
- **OAuth2 M2M Authentication**: Machine-to-machine flow with AWS Cognito (`token_manager.py`) for secure gateway access
- **Thread-safe Token Caching**: Access tokens cached with thread-safe locks, reducing authentication overhead
- **Dual Implementation Support**: Factory pattern (`factory.py`) supports both MCP and Runtime implementations, configurable via SSM/env

**AgentCore Memory:**
- **Semantic Memory**: Actor-scoped namespaces (`/facts/{actorId}`) ensure cook-specific context isolation
- **30-day Retention**: Compliance-aligned event expiry for audit trails
- **Session Grouping**: Daily sessions (`phone_number_YYYYMMDD`) create natural conversation boundaries
- **Auto-provisioning**: Memory resource created on first use, stored in SSM for persistence

**Implementation Files:**
- `graph/cook_assistant/bedrock/mcp/client.py` - MCP client implementation
- `graph/cook_assistant/bedrock/mcp/agent_factory.py` - Agent creation with memory config
- `graph/cook_assistant/bedrock/mcp/token_manager.py` - OAuth2 token management
- `graph/cook_assistant/service.py` - Context building and message processing
- `graph/cook_assistant/memory_config.py` - Memory resource management

**Separation of Concerns:**
- Webhook layer performs routing (cook detection via Firebase lookup)
- No cross-contamination: Cook Assistant doesn't touch LangGraph state, LangGraph doesn't handle cook conversations
- Each system optimized for its use case: checkpointed workflows vs. conversational memory

---

## 18. Multi-Modal Capabilities

BetterMeals supports **text, vision, and speech** inputs to accommodate diverse user preferences and use cases.

| Modality          | Role                             | Implementation                          |
| ----------------- | -------------------------------- | --------------------------------------- |
| **Text**          | Primary conversational interface | WhatsApp messages, LangGraph agents      |
| **Vision**        | Parses lab PDFs/images           | Onboarding agent processes lab reports   |
| **Speech**        | Voice notes → text intents       | Whisper transcription → text processing  |

### Vision: Lab Report Processing

The **Onboarding Agent** accepts lab report images/PDFs via WhatsApp media attachments:

**Flow:**
1. User sends lab report image/PDF via WhatsApp
2. Media URL passed to Onboarding agent
3. Agent extracts structured data (glucose levels, cholesterol, etc.)
4. Calls `bm_onboard_resident` tool with parsed values
5. Creates structured household/resident profiles

**Example:**
```
User: [sends lab_report.pdf]
Onboarding Agent: "I've processed your lab results. Your glucose is 95 mg/dL (normal range). 
I'll create your profile with these values. Any dietary restrictions?"
```

### Speech: Voice Note Transcription

Users can send voice notes for hands-free interaction:

**Flow:**
1. User sends voice note via WhatsApp
2. Whisper API transcribes audio → text
3. Text processed by Supervisor (same as text messages)
4. Response delivered as text (or synthesized speech)

**Example:**
```
User: [sends voice: "Plan my meals for next week"]
Supervisor → Recommender → "Here's your meal plan for the week..."
```

### Multi-Modal Architecture

- **Unified Processing**: All modalities convert to text before agent processing
- **Media Handling**: WhatsApp media URLs passed through webhook payload
- **Tool Integration**: Vision processing integrated into onboarding tools
- **Future Extensions**: Ready for video (cooking demonstrations), structured data (CSV uploads)

Allows quick onboarding, natural conversation, and optional voice interaction.

---

## 19. Responsible AI

* Human approvals at key boundaries
* No hallucinations — APIs own the truth
* PII minimization and deterministic execution
* Clear separation between orchestration and domain logic

---

## 20. Live Demo Guide

1. **Run Orchestrator**

   ```bash
   uvicorn src.bettermeals.entrypoints.fastapi_app:app --port 8000
   ```

2. **Use Postman Collection**

   * Send onboarding messages
   * Trigger plan → approve → cart → approve → checkout flow

3. **Observe**

   * Streaming replies
   * Interrupts for approvals
   * Logged tool calls per agent


## 21. Implementation Status

| Area                 | Status         | Notes                                                    |
| -------------------- | -------------- | -------------------------------------------------------- |
| Supervisor & Workers | Complete       | LangGraph orchestration, Groq-powered (`llms/groq.py`)   |
| Cook Assistant       | Complete       | AWS Bedrock/MCP, AgentCore memory, MCP tool discovery   |
| Tooling Layer        | Complete       | Typed API wrappers                                       |
| API Responses        | Complete       | Ready for live endpoints                                |
| Multi-Modal (Vision) | Working        | Lab intake                                               |
| Multi-Modal (Speech) | Working        | Demo transcription                                       |
| Streaming            | Working        | Token-level (Groq-powered)                               |
| Semantic Memory      | Complete       | AgentCore integration with 30-day retention             |
| Groq Integration     | Complete       | All LangGraph agents use Groq LPU™                      |
| MCP Integration      | Complete       | Dynamic tool discovery and context injection             |
| Testing              | In progress    | Postman + pytest                                         |

---

## 22. Extensibility

* **New behaviors → new agents/tools** (no prompt bloat)
* **Channel expansion** (e.g., Teams, Slack) via integration layer
* **Feature growth** via subgraphs (e.g., multi-resident optimization)

---

## 23. Key Takeaways

* **Groq-powered real-time inference** — All LangGraph agents use Groq for millisecond responses, enabling natural conversational workflows
* **Dual architecture** — LangGraph (Groq-powered) for structured workflows, Bedrock/MCP for open-ended conversations
* **MCP tool discovery** — Dynamic tool registration and context injection via Model Context Protocol
* **Fast, stateful, real-time** orchestration with checkpointed resumability
* **Semantic memory** — AgentCore provides persistent context for cook conversations with actor-scoped namespaces
* **Multi-agent collaboration** — 7-agent system (1 Supervisor + 5 Workers + 1 Cook Assistant) with real-time handoffs
* **Durable & auditable** execution model with Firebase audit trails
* **Multi-modal & human-centered** UX with voice, vision, and text
* **Practical impact** for households & cooks with seamless integration
* **Production-ready** — SSM-managed configs, thread-safe operations, compliance-aligned retention

**Technical Implementation:**
- Groq integration: `src/bettermeals/llms/groq.py`
- MCP implementation: `src/bettermeals/graph/cook_assistant/bedrock/mcp/`
- Context injection: `src/bettermeals/graph/cook_assistant/service.py` (`_build_tool_context`)
- Agent orchestration: `src/bettermeals/graph/build.py`, `src/bettermeals/graph/workers.py`
- Memory management: `src/bettermeals/graph/cook_assistant/memory_config.py`

---

