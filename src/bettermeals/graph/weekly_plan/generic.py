from typing import Dict, Any
import logging

from .base import BaseWeeklyPlan, WeeklyPlanStep

# Configure logging
logger = logging.getLogger(__name__)


class GenericWeeklyPlan(BaseWeeklyPlan):
    """Weekly plan flow for generic users"""
    
    def get_weekly_plan_type(self) -> str:
        return "generic"
    
    def _initialize_steps(self) -> Dict[WeeklyPlanStep, callable]:
        return {
            WeeklyPlanStep.STARTED: self.start_plan_approval,
            WeeklyPlanStep.PLAN_APPROVAL: self._handle_plan_approval,
            # WeeklyPlanStep.SUBSTITUTION_SELECTION: self._handle_substitution_selection,
            # WeeklyPlanStep.CHECKOUT_CONFIRMATION: self._handle_checkout_confirmation,
        }
    
    def _handle_plan_approval(self, text: str, phone_number: str, household_id: str) -> Dict[str, Any]:
        """Handle plan approval step."""
        # Check if user has approved the plan
        approved = text.lower().strip() in ["approved", "approve", "yes", "y", "yeah", "yep", "ok", "okay"]
        
        if approved:
            self._set_weekly_plan_step(phone_number, WeeklyPlanStep.COMPLETED)
            self._save_final_weekly_plan_data(phone_number)
            
            return {
                "reply": "Great! Thanks for confirming your preferences for the week."
            }
        else:
            # Keep asking for approval
            return {
                "reply": "Please review your weekly meal plan first at: https://bettermeals.in/app/dashboard/{household_id} to move ahead."
            }
    
    def start_plan_approval(self, text: str, phone_number: str, household_id: str) -> Dict[str, Any]:
        """Start the plan approval process for a user."""
        try:
            self._set_weekly_plan_step(phone_number, WeeklyPlanStep.PLAN_APPROVAL)

            approval_link = f"https://bettermeals.in/app/dashboard/{household_id}"
            
            if household_id:
                response = {
                    "reply": f"Welcome to your weekly meal planning! 🍽️\n\nYour personalized meal plan is ready!\n\nPlease review and approve your meal plan at: {approval_link}\n\nOnce you've reviewed the plan, reply with 'approved' to confirm."
                }
            else:
                response = {
                    "reply": f"Welcome to your weekly meal planning! 🍽️\n\nPlease review and approve your meal plan at: {approval_link}\n\nOnce you've reviewed the plan, reply with 'approved' to confirm."
                }
            
            # Save the initial message
            self._save_message(household_id, "bot", response["reply"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error starting plan approval for {household_id}: {str(e)}")
            return {"reply": "Sorry, I encountered an error starting your meal planning. Please try again."}
