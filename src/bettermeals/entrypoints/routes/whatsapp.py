from fastapi import APIRouter, Depends
from ...utils.webhook_processor import WebhookProcessor
from ...graph.service import graph_service
from ...graph.onboarding import onboarding_service
from ...graph.weekly_plan import weekly_plan_service
from ...graph.cook_assistant import cook_assistant_service
from ...graph.user_agent import user_agent_service

router = APIRouter()


def get_graph():
    """Dependency to get the graph instance."""
    return graph_service.get_graph()


@router.post("/whatsapp")
async def whatsapp_webhook(req: dict, graph=Depends(get_graph)):
    """Handle incoming WhatsApp webhook requests."""
    phone_number = req.get("phone_number")
    is_cook = cook_assistant_service.is_cook(phone_number)
    if is_cook:
        return await cook_assistant_service.process_cook_message(req)
    household_data = onboarding_service.get_household_data(phone_number)
    is_onboarded = household_data is not None and household_data.get("onboarding", {}).get("status") == "completed"
    
    ### Onboard new users (new phone numbers)
    if not is_onboarded:
        return onboarding_service.process_onboarding_message(req)

    ### First thing each week is to approve the weekly plan
    weekly_plan_locked = weekly_plan_service.is_weekly_plan_locked(req, household_data)
    if not weekly_plan_locked:
        return weekly_plan_service.process_weekly_plan_message(req, household_data)
    
    return await user_agent_service.process_messages(req)
