from fastapi import APIRouter, Request
from ...graph.build import build_graph
from ...graph.persistence import make_checkpointer

router = APIRouter()
graph = build_graph(checkpointer=make_checkpointer())

@router.post("/whatsapp")
async def whatsapp_webhook(req: Request):
    payload = await req.json()
    text = payload.get("text", "")
    household_id = payload.get("thread_id") or payload.get("household_id", "demo_household")
    sender_role = payload.get("sender_role", "user")
    config = {"configurable": {"thread_id": household_id}}
    state_in = {
        "messages": [{"role": "user", "content": text}],
        "household_id": household_id,
        "sender_role": sender_role,
    }
    # Non-blocking stream is possible; keeping it simple with ainvoke
    final = await graph.ainvoke(state_in, config)
    # Minimal mapping for demo; in production convert to WhatsApp message structure
    return {"reply": final.get("api_result") or "Acknowledged"}
