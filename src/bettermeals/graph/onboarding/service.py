from typing import Dict, Any, Optional, Tuple
import logging

from .generic_v2 import GenericUserOnboardingV2
from .referral import ReferralUserOnboarding
from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class OnboardingService:
    """Service to manage different onboarding flows (generic, referral, etc.)"""

    def __init__(self):
        self.generic_onboarding = GenericUserOnboardingV2()
        self.referral_onboarding = ReferralUserOnboarding()
        # TODO: In production, we might load these dynamically or from a config

    def get_household_data(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if user is already onboarded based on webhook payload."""
        try:
            if phone_number is None or phone_number == "":
                logger.info("No phone number found in payload")
                return None
                
            logger.info(f"Checking onboarding status for phone: {phone_number}")
            household_data = self.get_household_from_phone_num(phone_number)
            return household_data
            
        except Exception as e:
            logger.error(f"Error checking onboarding status: {str(e)}")
            return None
    
    def check_if_onboarding_form_submitted(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if user is already onboarded based on webhook payload."""
        try:
            if phone_number is None or phone_number == "":
                logger.info("No phone number found in payload")
                return False, None
                
            logger.info(f"Checking onboarding status for phone: {phone_number}")
            household_data = self.get_household_from_phone_num(phone_number)
            
            # User is considered onboarded if they have household data
            is_onboarded = household_data is not None
            logger.info(f"User {phone_number} onboarded status: {is_onboarded}")
            return is_onboarded, household_data
            
        except Exception as e:
            logger.error(f"Error checking onboarding status: {str(e)}")
            return False, None

    def get_household_from_phone_num(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get household data for a given phone number."""
        try:
            logger.info(f"Getting household data for phone: {phone_number}")
            db = get_db()
            user = db.find_user_by_phone(phone_number)
            
            if user is None:
                logger.info(f"No user found for phone: {phone_number}")
                return None
                
            household_id = user.get("householdId")
            if household_id is None:
                logger.warning(f"User {phone_number} has no householdId")
                return None
                
            household = db.get_household_data(household_id)
            logger.info(f"Retrieved household data for phone: {phone_number}")
            return household
            
        except Exception as e:
            logger.error(f"Error getting household data for phone {phone_number}: {str(e)}")
            return None

    def process_onboarding_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process onboarding message and return appropriate response."""
        try:
            phone_number = payload.get("phone_number")
            text = payload.get("text", "").strip()
            
            # Determine onboarding type based on payload or other logic
            onboarding_type = self._determine_onboarding_type(payload)
            
            if onboarding_type == "referral":
                return self.referral_onboarding.process_message(text, phone_number)
            else:
                return self.generic_onboarding.process_message(text, phone_number)
                
        except Exception as e:
            logger.error(f"Error processing onboarding message: {str(e)}")
            return {"reply": "Sorry, I encountered an error. Please try again."}

    def _determine_onboarding_type(self, payload: Dict[str, Any]) -> str:
        """Determine the type of onboarding based on payload or other logic."""
        # For now, check if there's a referral code or other indicators
        # In production, this could check database, URL parameters, etc.
        referral_code = payload.get("referral_code")
        if referral_code:
            return "referral"
        return "generic"


# Create a singleton instance
onboarding_service = OnboardingService()
