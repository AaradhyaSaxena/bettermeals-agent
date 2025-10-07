# Technical Evaluation

## 1. Executive Summary

This system provides an end-to-end automation pipeline that transforms **personal context (labs, preferences, constraints)** into a **weekly meal plan**, a **scored nutritional summary**, and an **actionable grocery cart**, with optional automated checkout - all while keeping **humans in control at key decision points**.

Key features include:

- **Multi-agent orchestration** using a Supervisor–Worker model.  
- **Deterministic, API-first decision making**, with tools as the single source of truth.  
- **Low-latency streaming interactions** for real-time responsiveness.  
- **Multi-modal intake** (text, vision, optional speech).  
- **Durable execution** with checkpointing, idempotency, and resumability.  
- **Security & privacy by design**, with minimal PII and clear boundaries between orchestration and data sources.

---

## 2. Architecture Overview

### 2.1 High-Level Structure

- **User Interface:** WhatsApp is the primary inbound/outbound channel, enabling a natural conversational flow with users and household cooks.  
- **Integration Layer:** An n8n bridge handles inbound webhooks, sanitization, deduplication, and thread mapping before forwarding to the orchestrator.  
- **Orchestration Layer:** A LangGraph-based orchestrator coordinates multiple agents, manages state transitions, checkpoints, and streaming updates.  
- **Domain Logic Layer:** All nutritional, planning, and order decisions are made through structured HTTP tool calls to a dedicated API service. No agent invents domain facts.

### 2.2 Agent Roles

| Agent              | Responsibility |
|---------------------|---------------|
| **Supervisor**      | Routes intent, enforces policies, delegates to workers, manages interrupts. |
| **Onboarding**      | Converts text and lab PDFs/images into structured household profiles. |
| **Meal Recommender**| Generates meal plans via API calls, stores plan IDs and summaries. |
| **Meal Scorer**     | Scores plans and explains trade-offs based on API results. |
| **Order Manager**   | Builds carts, handles substitutions, manages checkout and delivery tracking. |
| **Cook Update**     | Interprets messages from cooks and translates them into structured substitutions. |

### 2.3 Tooling Surface

- All worker agents interact with external systems exclusively via **explicit, typed tool definitions** (HTTP endpoints).  
- Tools are discoverable and auditable; capabilities are scoped per agent.

---

## 3. Model & Modalities

The system supports multiple input modalities:

- **Text** - WhatsApp messages drive all conversation flows.  
- **Vision** - Lab reports (PDFs or images) are parsed into structured JSON during onboarding.  
- **Speech** - Voice notes are transcribed and routed as text for intent classification.

Models are chosen to optimize for:
- **Fast response times** for conversational UX.  
- **Structured extraction** from semi-structured lab reports.  
- **Robust intent understanding** in multilingual, informal text contexts.

---

## 4. Performance Benchmarks

The orchestration layer is optimized for low-latency, real-time interactions.

| Metric                          | Target              | Notes |
|---------------------------------|----------------------|-------|
| **Time to First Token (TTFT)**  | 150–300 ms          | Ensures fast perceived responsiveness. |
| **P95 step latency**            | < 2.5 s             | Includes model + tool call. |
| **Supervisor loop latency**     | < 400 ms           | Routing + delegation per cycle. |
| **End-to-end flow**             | Under 25 s typical | From initial plan request to grocery cart build, excluding user delays. |

### How to Run Benchmarks
```bash
python perf/latency_probe.py --runs 50
````

The script produces:

* CSV with raw latencies
* Histogram of TTFT and step durations
* Simple textual summary of P50 / P95 numbers

---

## 5. Real-World Impact

* **Household Meal Planning:** Replaces ad-hoc chats and spreadsheets with structured weekly plans.
* **Human Approvals:** Users stay in control at key points - plan approval, substitutions, and checkout.
* **Cooks as Participants:** Cook messages are integrated seamlessly for substitutions and prep updates.
* **Predictable Spend:** Idempotent checkout flow prevents duplicate orders and supports budget control.
* **Less Friction:** Checkpoints and resumable execution reduce repeated manual work after interruptions.

---

## 6. Multi-Modal Capabilities

| Modality              | Role                                                  |
| --------------------- | ----------------------------------------------------- |
| **Text**              | Primary conversational interface (WhatsApp).          |
| **Vision**            | Parses lab PDFs/images to personalize meal planning.  |
| **Speech (Optional)** | Handles voice notes from users for intent extraction. |

This combination allows users to onboard quickly (by sending lab reports), converse naturally, and optionally use voice when convenient.

---

## 7. Responsible AI, Security & Privacy

* **Human Oversight:** All financial and nutritional decisions require explicit user approval.
* **No Hallucination:** Agents never generate nutritional data; they defer to authoritative APIs.
* **PII Minimization:** Personal identifiers are hashed or redacted; secrets are never stored in state.
* **Durability & Safety:** Checkpointing + idempotent API calls guarantee recoverable flows.
* **Clear Boundaries:** Orchestration and domain logic remain strictly separated for auditability.

---

## 8. Live Demo Guide

A short, reproducible demo flow highlights system behavior:

1. **Run the orchestrator locally**

   ```bash
   uvicorn src.bettermeals.entrypoints.fastapi_app:app --port 8000
   ```

2. **Use the Postman collection**

   * Send onboarding messages with or without lab reports.
   * Trigger a full plan → approve → cart → approve → checkout flow.

3. **Observe**

   * Streaming replies in terminal.
   * Interrupts at approvals.
   * Logged tool calls per agent.

---

## 9. Extensibility

The system is modular by design:

* **Adding new behaviors** → create new agents or tools without changing Supervisor logic.
* **Channel expansion** → swap WhatsApp for Teams/Slack by changing only the integration layer.
* **Feature growth** → add subgraphs (e.g., multi-resident optimization) without touching core flows.

---

## 11. Key Takeaways

* **Fast, stateful, and real-time** - designed for smooth conversational UX.
* **Durable and auditable** - checkpoints, idempotency, and scoped tool calls.
* **Multi-modal and human-centered** - lab intake, approvals, cook updates.
* **Practical impact** - solves a real coordination problem in households.

---
