from fastapi import APIRouter, Depends
from ...utils.webhook_processor import WebhookProcessor
from ...graph.service import graph_service
from ...graph.onboarding import onboarding_service
from ...graph.weekly_plan import weekly_plan_service

router = APIRouter()


def get_graph():
    """Dependency to get the graph instance."""
    return graph_service.get_graph()


@router.post("/whatsapp")
async def whatsapp_webhook(req: dict, graph=Depends(get_graph)):
    """Handle incoming WhatsApp webhook requests."""
    phone_number = req.get("phone_number")
    household_data = onboarding_service.get_household_data(phone_number)
    is_onboarded = household_data and household_data.get("onboarding", {}).get("status") == "completed"
    
    ### Onboard new users (new phone numbers)
    if not is_onboarded:
        return onboarding_service.process_onboarding_message(req)

    ### First thing each week is to approve the weekly plan
    weekly_plan_locked = weekly_plan_service.is_weekly_plan_locked(req, household_data)
    if not weekly_plan_locked:
        return weekly_plan_service.process_weekly_plan_message(req, household_data)
    
    return {
        "reply": "Hi, How can I help you today?"
    }
    # text, household_id, sender_role = WebhookProcessor.extract_payload_data(req)
    # state_in, config = WebhookProcessor.build_graph_input(text, household_id, sender_role)
    # final = await graph.ainvoke(state_in, config)
    
    # messages = final.get("messages", [])
    # WebhookProcessor.debug_print_messages(messages)
    # last_message = WebhookProcessor.extract_last_ai_message(messages)
    
    # response = WebhookProcessor.build_response(last_message, final)
    # print(f"Response: {response}")
    # return response
