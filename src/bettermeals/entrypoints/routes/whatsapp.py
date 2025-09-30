from fastapi import APIRouter, Request
import json
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
    
    # Debug: Print all messages to see what's happening
    print("=== DEBUG: All Messages ===")
    messages = final.get("messages", [])
    for i, msg in enumerate(messages):
        print(f"Message {i}: {type(msg).__name__}")
        if hasattr(msg, 'name'):
            print(f"  Name: {msg.name}")
        if hasattr(msg, 'content'):
            print(f"  Content: {msg.content[:100]}...")
        if hasattr(msg, 'tool_calls'):
            print(f"  Tool calls: {msg.tool_calls}")
        print("---")
    
    last_message = None
    for msg in reversed(messages):
        # Handle LangChain message objects
        if hasattr(msg, 'content') and msg.content:
            # Check if it's an AI message (not from user)
            if hasattr(msg, 'name') and msg.name != 'user':
                last_message = msg.content
                break
            elif hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                last_message = msg.content
                break
    
    # Return the actual response with any pending actions
    response = {"reply": last_message or "I'm processing your request..."}
    
    # Include pending action if present (for human-in-the-loop)
    if final.get("pending_action"):
        response["pending_action"] = final["pending_action"]
    
    print(f"Response: {response}")
    return response
