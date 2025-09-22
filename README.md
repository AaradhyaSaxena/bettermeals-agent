# BetterMeals Agent — Mini Design Doc 

## 1) Problem & Goals

**Problem.** We need a reliable, stateful automation that turns labs + preferences into a weekly meal plan, groceries, and (optionally) an auto-checkout, while coordinating over WhatsApp with human approvals.

**Goals:**
- Deterministic, auditable orchestration with resumability and human-in-the-loop approvals
- WhatsApp-first UX (Meta Cloud API) via n8n webhooks + sends
- Pluggable "smart" modules (parsers, planners) and "unsafe" side-effects behind approvals (e.g., Playwright checkout on BigBasket)
- Easy rollback/retry and artifact traceability (plans, lists, receipts)

**Non‑Goals.** Full nutrition domain models, enterprise-grade analytics, or multi-tenant billing in v1.

## 2) High-Level Architecture


![High-Level Architecture](data/agent-hld.png)




**Runtime split:**
- **LangGraph:** business logic, state machine, retries, approvals (interrupts), artifact lineage
- **n8n:** WhatsApp Cloud API (webhooks + sends), storage of WA media, integration glue (Sheets/Drive, CRM), rate limiting

## 3) Key Components

### 3.1 LangGraph Orchestrator
- **Nodes:** LabParser, ProfileMapper, MealPlanner, GroceryEngine, Checkout, Notify
- **Supervisor:** routes tasks to specialists; consolidates outputs; raises interrupts
- **Checkpointer:** Redis in prod (SQLite in dev). Stores per-thread state + artifacts
- **Artifacts store:** S3/GCS paths for lab files, plan JSON, grocery CSV, and receipts/screenshots

### 3.2 n8n Integration Layer
- **Inbound:** WhatsApp webhook → sanitize → dedupe on message_id → map phone_number → thread_id → call LangGraph /runs|/resume
- **Outbound:** Send session messages or templates; handle media upload (images/PDFs); retries with backoff
- **Storage:** small KV (n8n Postgres) for phone ↔ run_id mapping + last_seen window



## 4) State & Data Model (v1)

```typescript
// LangGraph Thread-State (simplified)
interface BMState {
  userId: string;              // whatsapp phone or internal uid
  stage: 'init'|'parsed'|'mapped'|'planned'|'approved_plan'|'groceries'|'checkout_pending'|'paid'|'done'|'error';
  inputs: {
    labsUrl?: string;          // signed URL from n8n upload
    preferences?: BMPreferences; // veg, dislikes, cook constraints
  };
  profile?: string;            // Profile1..5
  mealPlan?: MealPlan;         // structured JSON for day/meal/dishes
  groceryList?: GroceryItems[];
  approvals: Array<{type:'plan'|'checkout'; status:'await'|'approved'|'rejected'; ts:number; messageId?:string}>;
  receipts?: { orderId?: string; amount?: number; screenshotUrl?: string };
  logs: Array<{ts:number; msg:string; level:'info'|'warn'|'error'}>;
}
```

**Artifacts:** MealPlan.json, GroceryList.csv, CheckoutScreenshot.png, Receipt.json stored in S3/GCS; state keeps pointers.



## 5) Core Workflows
### 5.1 Inbound Message (n8n → LangGraph)
Receive WA message; ensure within 24‑h session or use template.


Dedupe by message_id.


If attachment (lab PDF/image): store → create signed URL.


POST to /runs (new) or /runs/{id}/resume with {thread_id, text, mediaUrls[]}.


### 5.2 Plan Generation (LangGraph)
LabParser extracts biomarkers → normalized table.


ProfileMapper picks Profile (1–5) and goals.


MealPlanner generates ≤45‑min, 3‑dish daily plan (your v1 constraint) and computes macro targets.


Interrupt: ApprovePlan → returns prompt & plan summary.


### 5.3 Groceries & Checkout
On approval, GroceryEngine subtracts pantry, rounds to pack sizes, outputs checklist.


Optional Checkout node (Playwright + BigBasket). Guarded by Interrupt: ApproveCheckout(amount).


On success, capture orderId + screenshot.


### 5.4 Notifications (n8n)
Send plan summary (carousel/text), grocery list file, and order status.


On rejection, route back to MealPlanner with constraints diff.



## 6) Human‑in‑the‑Loop
Interrupt points: ApprovePlan, ApproveCheckout (and optionally ApproveSubstitutions).


Resume semantics: n8n calls /runs/{id}/resume with {approval: 'yes'|'no', notes?: string}.


Timeouts: auto-cancel after N hours; state transitions to error or init.



## 7) Reliability, Errors, Observability
Retries: idempotent nodes (planner) use at‑least‑once; side‑effects (checkout) use exactly‑once guard via approval token + order status probe.


Compensation: if checkout fails after payment attempt, poll order status; if unknown, surface to human.


Metrics: run latency, success rate per node, WA delivery status, approval conversion, fallbacks.


Tracing: run_id, thread_id, and WA message_id stamped across n8n + LangGraph logs.



## 8) Security & Compliance
- **PII:** store phone numbers hashed; map to internal userId
- **Secrets:** WhatsApp tokens, Playwright creds via Vault/Env; never log raw tokens
- **Data retention:** expunge lab media after T days; keep derived aggregates
- **Opt‑out:** handle STOP/HELP keywords in n8n; propagate to LangGraph

## 9) Interfaces (HTTP)
- `POST /runs` → {thread_id, text?, mediaUrls?} → {run_id, status, next:'AWAITING_APPROVAL'|'IN_PROGRESS'|'DONE'}
- `POST /runs/{run_id}/resume` → {approval?:'yes'|'no', text?, notes?} → {status}
- `GET /runs/{run_id}` → state snapshot (redacted)



## 10) Milestones
- **M0 (Week 1):** LangGraph skeleton + checkpointer; n8n inbound/outbound echo; basic interrupts
- **M1 (Week 2):** LabParser + ProfileMapper + MealPlanner v1; ApprovePlan loop on WhatsApp
- **M2 (Week 3):** GroceryEngine v1 + file delivery; ApproveCheckout guard; sandbox checkout
- **M3 (Week 4):** Observability (metrics/logs), error handling, receipts; limited pilot

## 11) Open Questions
- Do we want AutoGen-style debate for MealPlanner quality before ApprovePlan?
- Where to store pantry inventory (per household) and who updates it (cook vs user)?
- Do we gate substitutions during checkout via a third interrupt?
- Preferred cloud (you have AWS credits) → pick S3 + Redis ElastiCache?
