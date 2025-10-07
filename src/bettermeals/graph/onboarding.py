from typing import Dict, Any, Optional
import logging

from src.bettermeals.database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class OnboardingService:
    """Service to onboard new users"""

    def check_if_onboarded(self, payload: Dict[str, Any]) -> bool:
        """Check if user is already onboarded based on webhook payload."""
        try:
            phone_number = payload.get("phone_number")
            if phone_number is None:
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

    def trigger_onboarding_flow(self, payload: Dict[str, Any]):
        """Trigger the onboarding flow for a given payload."""
        try:
            logger.info(f"Triggering onboarding flow for payload: {payload}")
            phone_number = payload.get("phone_number")

        except Exception as e:
            logger.error(f"Failed to onboard user: {str(e)}")
            raise


onboarding_service = OnboardingService()
