from typing import Dict, Any
import logging

from .base import BaseWorkflow, WorkflowStep

# Configure logging
logger = logging.getLogger(__name__)


class GenericChatWorkflow(BaseWorkflow):
    """Workflow flow for generic users"""

    def __init__(self):
        self.form_link = "form_link"
    
    def get_workflow_type(self) -> str:
        return "generic"
    
    def _initialize_steps(self) -> Dict[WorkflowStep, callable]:
        return {
            WorkflowStep.GREETING: self._handle_greeting,
            WorkflowStep.NAME_COLLECTION: self._handle_name_collection,
            WorkflowStep.FORM_COMPLETION: self._handle_form_completion,
            WorkflowStep.PAYMENT_CONFIRMATION: self._handle_payment_confirmation,
        }
    
    def _handle_greeting(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle initial greeting step."""
        self._set_workflow_step(phone_number, WorkflowStep.NAME_COLLECTION)
        return {
            "reply": "Hey! I'm Zuko from Bettermeals. May I know your name?"
        }
    
    def _handle_name_collection(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle name collection step."""
        name = text.strip()
        if not name:
            return {"reply": "Please tell me your name so I can help you better!"}
        
        # Store the name
        user_data = self._get_user_data(phone_number)
        user_data["name"] = name
        self._set_user_data(phone_number, user_data)
        
        self._set_workflow_step(phone_number, WorkflowStep.FORM_COMPLETION)
        return {
            "reply": f"Nice to meet you, {name}! Please complete this quick workflow form to get started: {self.form_link} \n\n Let me know once you've completed the form!"
        }
    
    def _handle_form_completion(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle form completion step."""
        completion_keywords = ["done", "completed", "finished"]
        # Import locally to avoid circular import
        from .service import workflow_service
        if any(keyword in text.lower() for keyword in completion_keywords) and workflow_service.check_if_workflow_form_submitted(phone_number)[0]:
            self._set_workflow_step(phone_number, WorkflowStep.COMPLETED)
            user_data = self._get_user_data(phone_number)
            user_name = user_data.get("name", "there")
            self._save_final_workflow_data(phone_number)
            # self._create_user_record(phone_number)
            return {
                "reply": f"Perfect, {user_name}! Thanks for completing the form. Let me know if you need anything else."
            }    
        else:
            return {
                "reply": "Please complete the workflow form first: {self.form_link} \n\nLet me know once you're done!"
            }
    
    def _create_user_record(self, phone_number: str):
        """Create user record in database after successful workflow."""
        try:
            user_data = self._get_user_data(phone_number)
            logger.info(f"Creating user record for {phone_number} with data: {user_data}")
            
            # TODO: For now, just log the completion
            logger.info(f"Generic workflow completed for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error creating user record for {phone_number}: {str(e)}")
