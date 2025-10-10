from csv import Error
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta

from .generic import GenericWeeklyPlan
from ...database.database import get_db
from ...config.ext_endpoints import call_generate_meal_plan

logger = logging.getLogger(__name__)


class WeeklyPlanService:
    """Service to manage different weekly plan flows (generic, premium, etc.)"""

    def __init__(self):
        self.generic_weekly_plan = GenericWeeklyPlan()
        # In production, we might load these dynamically or from a config

    def _get_current_week_number(self) -> int:
        """Get the current week number using ISO week format."""
        return (datetime.now() + timedelta(weeks=1)).strftime("%Y-%W")

    def is_weekly_plan_locked(self, payload: Dict[str, Any], household_data: Optional[Dict[str, Any]]) -> bool:
        """Check if weekly plan is locked (completed) for this user."""
        try:
            phone_number = payload.get("phone_number")
            
            if not household_data:
                raise ValueError(f"No household data for {phone_number}")
                
            current_week_num = self._get_current_week_number()
            # Check if weekly plan is already completed for the current week
            weekly_plan_data = household_data.get("weekly_plan", {})
            weekly_plan_status = weekly_plan_data.get("status")
            weekly_plan_week = weekly_plan_data.get("week")
            
            is_locked = (weekly_plan_status == "approved" and 
                        weekly_plan_week == current_week_num)
            
            logger.info(f"Weekly plan locked status for {phone_number}: {is_locked} "
                       f"(status: {weekly_plan_status}, week: {weekly_plan_week}, current_week: {current_week_num})")
            return is_locked
            
        except Exception as e:
            logger.error(f"Error checking weekly plan lock status: {str(e)}")
            return True

    def process_weekly_plan_message(self, payload: Dict[str, Any], household_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process weekly plan message and return appropriate response."""
        try:
            phone_number = payload.get("phone_number")
            if not household_data:
                raise ValueError(f"No household data for {phone_number}")
            text = payload.get("text", "").strip()
            household_id = household_data.get("householdId")

            logger.info(f"Trigger meal plan generation for household {household_id}")
            ############################
            # meal_plan_response = call_generate_meal_plan(household_id)
            meal_plan_response = True
            ############################
            if meal_plan_response is None:
                raise Exception(f"Error generating meal plan for household {household_id}")
            logger.info(f"Meal plan generated successfully for household {household_id}")
            
            # Determine weekly plan type based on payload or other logic
            weekly_plan_type = self._determine_weekly_plan_type(payload)
            
            if weekly_plan_type == "generic":
                return self.generic_weekly_plan.process_message(text, phone_number, household_id)
            else:
                # Default to generic for now
                return self.generic_weekly_plan.process_message(text, phone_number, household_id)
                
        except Exception as e:
            logger.error(f"Error processing weekly plan message: {str(e)}")
            return {"reply": "Sorry, I encountered an error. Please try again."}

    def _determine_weekly_plan_type(self, payload: Dict[str, Any]) -> str:
        """Determine the type of weekly plan based on payload or other logic."""
        # TODO: Add options. For now, always return generic.
        return "generic"


# Create a singleton instance
weekly_plan_service = WeeklyPlanService()
