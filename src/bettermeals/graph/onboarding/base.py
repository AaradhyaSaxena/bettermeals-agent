from typing import Dict, Any, Optional
import logging
from enum import Enum
from abc import ABC, abstractmethod

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
            # Get current onboarding state for this user
            current_step = self._get_current_onboarding_step(phone_number)
            logger.info(f"Processing {self.get_onboarding_type()} onboarding for {phone_number} at step: {current_step}")
            
            # Process the current step
            if current_step in self.onboarding_steps:
                response = self.onboarding_steps[current_step](text, phone_number)
                return response
            else:
                # Default fallback
                return {"reply": "Welcome to BetterMeals! Let's get you started. What's your name?"}
                
        except Exception as e:
            logger.error(f"Error processing {self.get_onboarding_type()} onboarding message: {str(e)}")
            return {"reply": "Sorry, I encountered an error. Please try again."}
    
    def _get_current_onboarding_step(self, phone_number: str) -> OnboardingStep:
        """Get the current onboarding step for a user."""
        # For now, we'll use a simple in-memory approach
        # In production, you'd store this in the database
        if not hasattr(self, '_onboarding_state'):
            self._onboarding_state = {}
        
        return self._onboarding_state.get(phone_number, OnboardingStep.GREETING)
    
    def _set_onboarding_step(self, phone_number: str, step: OnboardingStep):
        """Set the onboarding step for a user."""
        if not hasattr(self, '_onboarding_state'):
            self._onboarding_state = {}
        self._onboarding_state[phone_number] = step
    
    def _get_user_data(self, phone_number: str) -> Dict[str, Any]:
        """Get user data for a phone number."""
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        if phone_number not in self._user_data:
            self._user_data[phone_number] = {}
        return self._user_data[phone_number]
    
    def _set_user_data(self, phone_number: str, data: Dict[str, Any]):
        """Set user data for a phone number."""
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        self._user_data[phone_number] = data
