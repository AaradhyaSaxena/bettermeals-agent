from typing import Dict, Any, Optional
import logging
from enum import Enum
from abc import ABC, abstractmethod
from datetime import datetime

from ...database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    """Enumeration of workflow steps"""
    GREETING = "greeting"
    NAME_COLLECTION = "name_collection"
    FORM_COMPLETION = "form_completion"
    NEEDS_ASSESSMENT = "needs_assessment"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    COMPLETED = "completed"


class BaseWorkflow(ABC):
    """Base class for all workflows flows"""
    
    def __init__(self):
        self.workflow_steps = self._initialize_steps()
        self.workflow_transaction_collection_name = "workflow_transactions"
        self.workflow_status_collection_name = "workflow_status"
    
    @abstractmethod
    def _initialize_steps(self) -> Dict[WorkflowStep, callable]:
        """Initialize the step handlers for this workflow step type"""
        pass
    
    @abstractmethod
    def get_workflow_type(self) -> str:
        """Return the type of workflow (e.g., 'generic', 'referral')"""
        pass
    
    def process_message(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Process workflow message and return appropriate response."""
        try:
            # Save user message to database
            self._save_message(phone_number, "user", text)
            
            # Get current workflow state for this user
            current_step = self._get_current_workflow_step(phone_number)
            logger.info(f"Processing {self.get_workflow_type()} workflow for {phone_number} at step: {current_step}")
            
            # Process the current step
            if current_step in self.workflow_steps:
                response = self.workflow_steps[current_step](text, phone_number)
                
                # Save bot response to database
                if "reply" in response:
                    self._save_message(phone_number, "bot", response["reply"])
                
                return response
            else:
                # Default fallback
                fallback_response = {"reply": "Hi, how can I help you today?"}
                self._save_message(phone_number, "bot", fallback_response["reply"])
                return fallback_response
                
        except Exception as e:
            logger.error(f"Error processing {self.get_workflow_type()} workflow message: {str(e)}")
            error_response = {"reply": "Sorry, We're facing some trouble. Please try again."}
            self._save_message(phone_number, "bot", error_response["reply"])
            return error_response
    
    def _get_current_workflow_step(self, phone_number: str) -> WorkflowStep:
        """Get the current workflow step for a user from database."""
        try:
            db = get_db()
            messages = db.get_workflow_messages(phone_number, self.workflow_transaction_collection_name)
            filter_messages = self._filter_messages(messages)
            
            if not filter_messages:
                return WorkflowStep.GREETING
            
            # Find the latest step update (system message with step_update=True)
            latest_step = WorkflowStep.GREETING
            for message in filter_messages:  # Start from most recent
                if message.get("step_update") and message.get("role") == "system":
                    current_step_str = message.get("current_step", WorkflowStep.GREETING.value)
                    try:
                        latest_step = WorkflowStep(current_step_str)
                        break
                    except ValueError:
                        logger.warning(f"Invalid workflow step '{current_step_str}' for {phone_number}")
                        continue
            
            logger.debug(f"Current workflow step for {phone_number}: {latest_step.value}")
            return latest_step
            
        except Exception as e:
            logger.error(f"Error getting workflow step from database for {phone_number}: {str(e)}")
            return WorkflowStep.GREETING
    
    def _set_workflow_step(self, phone_number: str, step: WorkflowStep):
        """Set the workflow step for a user by saving it to database."""
        try:
            db = get_db()
            step_data = {
                "role": "system",
                "content": f"Step updated to: {step.value}",
                "workflow_type": self.get_workflow_type(),
                "current_step": step.value,
                "step_update": True
            }
            db.save_workflow_message(phone_number, step_data, self.workflow_transaction_collection_name)
            logger.debug(f"Updated workflow step to {step.value} for {phone_number}")
        except Exception as e:
            logger.error(f"Error setting workflow step for {phone_number}: {str(e)}")
    
    def _get_user_data(self, phone_number: str) -> Dict[str, Any]:
        """Get user data for a phone number from database."""
        try:
            db = get_db()
            messages = db.get_workflow_messages(phone_number)
            
            # Extract user data from messages
            user_data = {}
            for message in messages:
                if message.get("role") == "user":
                    # Extract data based on current step
                    current_step = message.get("current_step", "")
                    content = message.get("content", "")
                    if current_step == WorkflowStep.NAME_COLLECTION.value:
                        user_data["name"] = content
                    elif current_step == WorkflowStep.NEEDS_ASSESSMENT.value:
                        user_data["needs"] = content
                        user_data["has_cook"] = content.lower().strip() in ["yes", "y", "yeah", "yep"]
                    elif current_step == WorkflowStep.NEEDS_ASSESSMENT.value and "treatment_plan" in content.lower():
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
            current_step = self._get_current_workflow_step(phone_number)
            message_data = {
                "role": role,
                "content": content,
                "workflow_type": self.get_workflow_type(),
                "current_step": current_step.value
            }
            db.save_workflow_message(phone_number, message_data, self.workflow_transaction_collection_name)
            logger.debug(f"Saved {role} message for {phone_number} at step {current_step.value}")
        except Exception as e:
            logger.error(f"Error saving message for {phone_number}: {str(e)}")

    def _save_final_workflow_data(self, phone_number: str):
        """Save final workflow data to household collection."""
        try:
            db = get_db()
            
            # Get current user data
            user_data = self._get_user_data(phone_number)
            current_step = self._get_current_workflow_step(phone_number)
            
            # Prepare final workflow data
            workflow_data = {
                "phone_number": phone_number,
                "workflow_type": self.get_workflow_type(),
                "current_step": current_step.value,
                "user_data": user_data,
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            # Save to household collection
            success = db.save_final_workflow_data(phone_number, workflow_data, self.workflow_status_collection_name)
            if success:
                logger.info(f"Successfully saved final workflow data for {phone_number}")
            else:
                logger.error(f"Failed to save final workflow data for {phone_number}")
                
        except Exception as e:
            logger.error(f"Error saving final workflow data for {phone_number}: {str(e)}")

    def _filter_messages(self, messages):
        """Filter messages to only include messages that are relevant to the workflow."""
        return messages
