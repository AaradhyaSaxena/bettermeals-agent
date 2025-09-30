from typing import TypedDict, Optional, List, Dict, Any

class State(TypedDict, total=False):
    messages: List[Dict[str, Any]]      # truncated chat history
    household_id: str
    sender_role: str                     # "user" | "cook"
    intent: Optional[str]                # 'onboarding'|'recommend'|'score'|'order'|'cook_update'
    api_payload: Dict[str, Any]
    api_result: Dict[str, Any]
    meal_plan_id: Optional[str]
    pending_action: Optional[str]        # 'approve_plan'|'approve_substitution'|'approve_checkout'
    last_error: Optional[str]
    artifacts: Dict[str, Any]            # URLs to plan json, grocery csv, receipt
