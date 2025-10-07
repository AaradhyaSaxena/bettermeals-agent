from fastapi import APIRouter, Depends
from ...utils.webhook_processor import WebhookProcessor
from ...graph.service import graph_service
from ...graph.onboarding import onboarding_service

router = APIRouter()


def get_graph():
    """Dependency to get the graph instance."""
    return graph_service.get_graph()


@router.post("/whatsapp")
async def whatsapp_webhook(req: dict, graph=Depends(get_graph)):
    """Handle incoming WhatsApp webhook requests."""
    is_onboarded, hld_data = onboarding_service.check_if_onboarded(req)
    if not is_onboarded:
        ## trigger onboarding flow
        return {"reply": "You are not onboarded yet. Please onboard first."}
    else:
        text, household_id, sender_role = WebhookProcessor.extract_payload_data(req)
        state_in, config = WebhookProcessor.build_graph_input(text, household_id, sender_role)
        final = await graph.ainvoke(state_in, config)
        
        messages = final.get("messages", [])
        WebhookProcessor.debug_print_messages(messages)
        last_message = WebhookProcessor.extract_last_ai_message(messages)
        
        response = WebhookProcessor.build_response(last_message, final)
        print(f"Response: {response}")
        return response
