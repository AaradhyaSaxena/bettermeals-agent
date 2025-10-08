from typing import Dict, Any, Optional
import logging
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class WeeklyPlanStep(Enum):
    """Enumeration of weekly plan steps"""
    STARTED = "started"
    PLAN_APPROVAL = "plan_approval"
    SUBSTITUTION_SELECTION = "substitution_selection"
    CHECKOUT_CONFIRMATION = "checkout_confirmation"
    COMPLETED = "approved"


class BaseWeeklyPlan(ABC):
    """Base class for all weekly plan flows"""
    
    def __init__(self):
        self.weekly_plan_steps = self._initialize_steps()
    
    @abstractmethod
    def _initialize_steps(self) -> Dict[WeeklyPlanStep, callable]:
        """Initialize the step handlers for this weekly plan type"""
        pass
    
    @abstractmethod
    def get_weekly_plan_type(self) -> str:
        """Return the type of weekly plan (e.g., 'generic', 'premium')"""
        pass
    
    def process_message(self, text: str, phone_number: str, household_id: str) -> Dict[str, Any]:
        """Process weekly plan message and return appropriate response."""
        try:
            # Save user message to database
            self._save_message(phone_number, "user", text)
            
            # Get current weekly plan state for this user
            current_step = self._get_current_weekly_plan_step(phone_number)
            logger.info(f"Processing {self.get_weekly_plan_type()} weekly plan for {phone_number} at step: {current_step}")
            
            # Process the current step
            if current_step in self.weekly_plan_steps:
                response = self.weekly_plan_steps[current_step](text, phone_number, household_id)
                
                # Save bot response to database
                if "reply" in response:
                    self._save_message(phone_number, "bot", response["reply"])
                
                return response
            else:
                # Default fallback
                fallback_response = {"reply": "Let's start your weekly meal planning! Please approve your plan at the link provided."}
                self._save_message(phone_number, "bot", fallback_response["reply"])
                return fallback_response
                
        except Exception as e:
            logger.error(f"Error processing {self.get_weekly_plan_type()} weekly plan message: {str(e)}")
            error_response = {"reply": "Sorry, I encountered an error. Please try again."}
            self._save_message(phone_number, "bot", error_response["reply"])
            return error_response
    
    def _get_current_weekly_plan_step(self, phone_number: str) -> WeeklyPlanStep:
        """Get the current weekly plan step for a user from database."""
        try:
            db = get_db()
            messages = db.get_weekly_plan_messages(phone_number)
            
            if not messages:
                # No previous messages, start fresh
                return WeeklyPlanStep.STARTED
            
            # Find the latest step update (system message with step_update=True)
            latest_step = WeeklyPlanStep.PLAN_APPROVAL
            for message in messages:  # Start from most recent
                if message.get("step_update") and message.get("role") == "system":
                    current_step_str = message.get("current_step", WeeklyPlanStep.PLAN_APPROVAL.value)
                    try:
                        latest_step = WeeklyPlanStep(current_step_str)
                        break
                    except ValueError:
                        logger.warning(f"Invalid weekly plan step '{current_step_str}' for {phone_number}")
                        continue
            
            logger.debug(f"Current weekly plan step for {phone_number}: {latest_step.value}")
            return latest_step
            
        except Exception as e:
            logger.error(f"Error getting weekly plan step from database for {phone_number}: {str(e)}")
            return WeeklyPlanStep.PLAN_APPROVAL
    
    def _set_weekly_plan_step(self, household_id: str, step: WeeklyPlanStep):
        """Set the weekly plan step for a user by saving it to database."""
        try:
            db = get_db()
            step_data = {
                "role": "system",
                "content": f"Step updated to: {step.value}",
                "weekly_plan_type": self.get_weekly_plan_type(),
                "current_step": step.value,
                "step_update": True
            }
            db.save_weekly_plan_message(household_id, step_data)
            logger.debug(f"Updated weekly plan step to {step.value} for {household_id}")
        except Exception as e:
            logger.error(f"Error setting weekly plan step for {household_id}: {str(e)}")
    
    def _get_user_data(self, household_id: str) -> Dict[str, Any]:
        """Get user data for a phone number from database."""
        try:
            db = get_db()
            messages = db.get_weekly_plan_messages(household_id)
            
            # Extract user data from messages
            user_data = {}
            for message in messages:
                if message.get("role") == "user":
                    # Extract data based on current step
                    current_step = message.get("current_step", "")
                    content = message.get("content", "")
                    if current_step == WeeklyPlanStep.PLAN_APPROVAL.value:
                        user_data["plan_approval"] = content
                    elif current_step == WeeklyPlanStep.SUBSTITUTION_SELECTION.value:
                        user_data["substitution_selection"] = content
                    elif current_step == WeeklyPlanStep.CHECKOUT_CONFIRMATION.value:
                        user_data["checkout_confirmation"] = content
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user data from database for {household_id}: {str(e)}")
            return {}
    
    def _save_message(self, phone_number: str, role: str, content: str):
        """Save individual message to database."""
        try:
            db = get_db()
            current_step = self._get_current_weekly_plan_step(phone_number)
            message_data = {
                "role": role,
                "content": content,
                "weekly_plan_type": self.get_weekly_plan_type(),
                "current_step": current_step.value
            }
            db.save_weekly_plan_message(phone_number, message_data)
            logger.debug(f"Saved {role} message for {phone_number} at step {current_step.value}")
        except Exception as e:
            logger.error(f"Error saving message for {phone_number}: {str(e)}")

    def _save_final_weekly_plan_data(self, phone_number: str):
        """Save final weekly plan data to household collection."""
        try:
            db = get_db()
            
            # Get current user data
            user_data = self._get_user_data(phone_number)
            current_step = self._get_current_weekly_plan_step(phone_number)
            
            # Prepare final weekly plan data
            weekly_plan_data = {
                "phone_number": phone_number,
                "weekly_plan_type": self.get_weekly_plan_type(),
                "current_step": current_step.value,
                "user_data": user_data,
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            # Save to household collection
            success = db.save_final_weekly_plan_data(phone_number, weekly_plan_data)
            if success:
                logger.info(f"Successfully saved final weekly plan data for {phone_number}")
            else:
                logger.error(f"Failed to save final weekly plan data for {phone_number}")
                
        except Exception as e:
            logger.error(f"Error saving final weekly plan data for {phone_number}: {str(e)}")
