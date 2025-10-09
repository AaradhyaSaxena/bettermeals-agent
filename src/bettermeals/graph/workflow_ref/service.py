from typing import Dict, Any, Optional, Tuple
import logging

from .generic import GenericChatWorkflow
from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowService:
    """Service to manage different workflow flows (generic, referral, etc.)"""

    def __init__(self):
        self.generic_workflow = GenericChatWorkflow()
        # TODO: In production, we might load these dynamically or from a config

    def get_household_data(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        try:
            if phone_number is None or phone_number == "":
                logger.info("No phone number found in payload")
                return None
                
            logger.info(f"Checking workflow status for phone: {phone_number}")
            household_data = self.get_household_from_phone_num(phone_number)
            return household_data
            
        except Exception as e:
            logger.error(f"Error checking workflow status: {str(e)}")
            return None
    
    def check_if_workflow_form_submitted(self, phone_number: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Ccheck if user submitted that form"""
        try:
            # db = get_db()
            ### check if user submitted that particular form
            pass
            
        except Exception as e:
            pass

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

    def process_workflow_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process workflow message and return appropriate response."""
        try:
            phone_number = payload.get("phone_number")
            text = payload.get("text", "").strip()
            
            # Determine workflow type based on payload or other logic
            workflow_type = self._determine_workflow_type(payload)
            
            if workflow_type == "referral":
                return self.generic_workflow.process_message(text, phone_number)
            else:
                return self.generic_workflow.process_message(text, phone_number)
                
        except Exception as e:
            logger.error(f"Error processing workflow message: {str(e)}")
            return {"reply": "Sorry, I encountered an error. Please try again."}

    def _determine_workflow_type(self, payload: Dict[str, Any]) -> str:
        """Determine the type of workflow based on payload or other logic."""
        # TODO: For now, check if there's a referral code or other indicators
        referral_code = payload.get("referral_code")
        if referral_code:
            return "referral"
        return "generic"


# Create a singleton instance
workflow_service = WorkflowService()
