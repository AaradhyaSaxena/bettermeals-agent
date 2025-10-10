from typing import Dict, Any
import logging

from .base import BaseWeeklyPlan, WeeklyPlanStep
from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class GenericWeeklyPlan(BaseWeeklyPlan):
    """Weekly plan flow for generic users"""

    def __init__(self):
        super().__init__()
        self.form_link = "https://bettermeals.in/app/dashboard/"
    
    def get_form_link(self, household_id: str):
        return self.form_link + household_id

    def get_weekly_plan_type(self) -> str:
        return "generic"
    
    def _initialize_steps(self) -> Dict[WeeklyPlanStep, callable]:
        return {
            WeeklyPlanStep.STARTED: self.start_plan_approval,
            WeeklyPlanStep.PLAN_APPROVAL: self._handle_plan_approval,
        }
    
    def start_plan_approval(self, text: str, phone_number: str, household_id: str) -> Dict[str, Any]:
        """Start the plan approval process for a user."""
        try:
            self._set_weekly_plan_step(phone_number, WeeklyPlanStep.PLAN_APPROVAL)
            approval_link = self.get_form_link(household_id)

            response = {
                "reply": f"Your weekly plan approval is pending for this week!\n\nPlease review and approve your meal plan at: {approval_link}\n\nOnce you've reviewed the plan, reply with 'approved' to confirm."
            }

            # Saving the initial message
            self._save_message(phone_number, "bot", response["reply"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error starting plan approval for {household_id}: {str(e)}")
            return {"reply": "Sorry, we're facing some issue reagarding your meal planning. Please try again."}
    
    def _handle_plan_approval(self, text: str, phone_number: str, household_id: str) -> Dict[str, Any]:
        """Handle plan approval step."""
        # Check if user has approved the plan
        completion_keywords = ["done", "completed", "finished","approved", "approve", "yes", "y", "yeah", "yep", "ok", "okay"]
        if any(keyword in text.lower() for keyword in completion_keywords) and self.check_if_workflow_form_submitted(household_id):
            self._set_weekly_plan_step(phone_number, WeeklyPlanStep.COMPLETED)
            self._save_final_weekly_plan_data(phone_number, household_id)
            
            return {
                "reply": "Great! Thanks for confirming your preferences for the week."
            }
        else:
            # Keep asking for approval
            approval_link = self.get_form_link(household_id)
            return {
                "reply": f"Please review your weekly meal plan first at: {approval_link} to move ahead."
            }
    
    def check_if_workflow_form_submitted(self, household_id: str) -> bool:
        """Check if workflow form is submitted for a user."""
        db = get_db()
        return db.check_if_weekly_plan_completed(household_id)