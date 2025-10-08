from typing import Dict, Any, Optional
import logging
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Enumeration of onboarding steps"""
    GREETING = "greeting"
    NAME_COLLECTION = "name_collection"
    FORM_COMPLETION = "form_completion"
    NEEDS_ASSESSMENT = "needs_assessment"
    STRESS_POINTS = "stress_points"
    COOK_COORDINATION_DETAILS = "cook_coordination_details"
    COOK_STATUS = "cook_status"
    TRIAL_OFFER = "trial_offer"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    GROUP_INVITATION = "group_invitation"
    COMPLETED = "completed"


class BaseOnboarding(ABC):
    """Base class for all onboarding flows"""
    
    def __init__(self):
        self.onboarding_steps = self._initialize_steps()
    
    @abstractmethod
    def _initialize_steps(self) -> Dict[OnboardingStep, callable]:
        """Initialize the step handlers for this onboarding type"""
        pass
    
    @abstractmethod
    def get_onboarding_type(self) -> str:
        """Return the type of onboarding (e.g., 'generic', 'referral')"""
        pass
    
    def process_message(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Process onboarding message and return appropriate response."""
        try:
            # Save user message to database
            self._save_message(phone_number, "user", text)
            
            # Get current onboarding state for this user
            current_step = self._get_current_onboarding_step(phone_number)
            logger.info(f"Processing {self.get_onboarding_type()} onboarding for {phone_number} at step: {current_step}")
            
            # Process the current step
            if current_step in self.onboarding_steps:
                response = self.onboarding_steps[current_step](text, phone_number)
                
                # Save bot response to database
                if "reply" in response:
                    self._save_message(phone_number, "bot", response["reply"])
                
                return response
            else:
                # Default fallback
                fallback_response = {"reply": "Welcome to BetterMeals! Let's get you started. What's your name?"}
                self._save_message(phone_number, "bot", fallback_response["reply"])
                return fallback_response
                
        except Exception as e:
            logger.error(f"Error processing {self.get_onboarding_type()} onboarding message: {str(e)}")
            error_response = {"reply": "Sorry, I encountered an error. Please try again."}
            self._save_message(phone_number, "bot", error_response["reply"])
            return error_response
    
    def _get_current_onboarding_step(self, phone_number: str) -> OnboardingStep:
        """Get the current onboarding step for a user from database."""
        try:
            db = get_db()
            messages = db.get_onboarding_messages(phone_number)
            
            if not messages:
                # No previous messages, start fresh
                return OnboardingStep.GREETING
            
            # Find the latest step update (system message with step_update=True)
            latest_step = OnboardingStep.GREETING
            for message in reversed(messages):  # Start from most recent
                if message.get("step_update") and message.get("role") == "system":
                    current_step_str = message.get("current_step", OnboardingStep.GREETING.value)
                    try:
                        latest_step = OnboardingStep(current_step_str)
                        break
                    except ValueError:
                        logger.warning(f"Invalid onboarding step '{current_step_str}' for {phone_number}")
                        continue
            
            logger.debug(f"Current onboarding step for {phone_number}: {latest_step.value}")
            return latest_step
            
        except Exception as e:
            logger.error(f"Error getting onboarding step from database for {phone_number}: {str(e)}")
            return OnboardingStep.GREETING
    
    def _set_onboarding_step(self, phone_number: str, step: OnboardingStep):
        """Set the onboarding step for a user by saving it to database."""
        try:
            db = get_db()
            step_data = {
                "role": "system",
                "content": f"Step updated to: {step.value}",
                "onboarding_type": self.get_onboarding_type(),
                "current_step": step.value,
                "step_update": True
            }
            db.save_onboarding_message(phone_number, step_data)
            logger.debug(f"Updated onboarding step to {step.value} for {phone_number}")
        except Exception as e:
            logger.error(f"Error setting onboarding step for {phone_number}: {str(e)}")
    
    def _get_user_data(self, phone_number: str) -> Dict[str, Any]:
        """Get user data for a phone number from database."""
        try:
            db = get_db()
            messages = db.get_onboarding_messages(phone_number)
            
            # Extract user data from messages
            user_data = {}
            for message in messages:
                if message.get("role") == "user":
                    # Extract data based on current step
                    current_step = message.get("current_step", "")
                    content = message.get("content", "")
                    if current_step == OnboardingStep.NAME_COLLECTION.value:
                        user_data["name"] = content
                    elif current_step == OnboardingStep.NEEDS_ASSESSMENT.value:
                        user_data["needs"] = content
                    elif current_step == OnboardingStep.STRESS_POINTS.value:
                        user_data["stress_points"] = content
                    elif current_step == OnboardingStep.COOK_COORDINATION_DETAILS.value:
                        user_data["cook_coordination_details"] = content
                    elif current_step == OnboardingStep.COOK_STATUS.value:
                        user_data["has_cook"] = content.lower().strip() in ["yes", "y", "yeah", "yep"]
                    elif current_step == OnboardingStep.NEEDS_ASSESSMENT.value and "treatment_plan" in content.lower():
                        user_data["treatment_plan"] = content
                        user_data["is_referral"] = True
                        user_data["referral_source"] = "Super Health Hospital"
            
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user data from database for {phone_number}: {str(e)}")
            return {}
    
    def _set_user_data(self, phone_number: str, data: Dict[str, Any]):
        """Set user data for a phone number - data is saved in messages."""
        # User data is automatically saved in messages, no local storage needed
        # This method is kept for compatibility but doesn't store anything locally
        pass

    def _save_message(self, phone_number: str, role: str, content: str):
        """Save individual message to database."""
        try:
            db = get_db()
            current_step = self._get_current_onboarding_step(phone_number)
            message_data = {
                "role": role,
                "content": content,
                "onboarding_type": self.get_onboarding_type(),
                "current_step": current_step.value
            }
            db.save_onboarding_message(phone_number, message_data)
            logger.debug(f"Saved {role} message for {phone_number} at step {current_step.value}")
        except Exception as e:
            logger.error(f"Error saving message for {phone_number}: {str(e)}")

    def _save_final_onboarding_data(self, phone_number: str):
        """Save final onboarding data to household collection."""
        try:
            db = get_db()
            
            # Get current user data
            user_data = self._get_user_data(phone_number)
            current_step = self._get_current_onboarding_step(phone_number)
            
            # Prepare final onboarding data
            onboarding_data = {
                "phone_number": phone_number,
                "onboarding_type": self.get_onboarding_type(),
                "current_step": current_step.value,
                "user_data": user_data,
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            # Save to household collection
            success = db.save_final_onboarding_data(phone_number, onboarding_data)
            if success:
                logger.info(f"Successfully saved final onboarding data for {phone_number}")
            else:
                logger.error(f"Failed to save final onboarding data for {phone_number}")
                
        except Exception as e:
            logger.error(f"Error saving final onboarding data for {phone_number}: {str(e)}")
