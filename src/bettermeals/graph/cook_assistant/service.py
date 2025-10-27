from typing import Dict, Any
import logging
from datetime import datetime
from ...database.database import get_db
from .bedrock_client import invoke_cook_assistant

logger = logging.getLogger(__name__)


class CookAssistantService:
    """Service to manage cook assistant interactions"""

    def __init__(self):
        self.db = get_db()

    def is_cook(self, phone_number: str) -> bool:
        """Check if phone number belongs to a cook"""
        try:
            if not phone_number:
                return False
            
            cook_data = self.db.find_cook_by_phone(phone_number)
            is_cook = cook_data is not None
            logger.info(f"Cook check for {phone_number}: {is_cook}")
            return is_cook
            
        except Exception as e:
            logger.error(f"Error checking cook status for {phone_number}: {str(e)}")
            return False

    async def process_cook_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process cook assistant message with AgentCore memory integration"""
        try:
            phone_number = payload.get("phone_number")
            text = payload.get("text", "").strip()
            
            if not phone_number or not text:
                return {"reply": "I need your message to help you. What would you like to know?"}
            
            logger.info(f"Processing cook message from {phone_number}: {text}")
            
            # Save user message to Firebase for audit/compliance
            self._save_message(phone_number, "user", text)
            
            # Generate session ID (phone_number + date for daily grouping)
            session_id = self._get_or_create_session_id(phone_number)
            
            # Invoke bedrock agent with AgentCore memory
            try:
                response_text = await invoke_cook_assistant(text, phone_number, session_id)
            except Exception as e:
                logger.error(f"Error invoking bedrock agent: {str(e)}")
                response_text = "I'm sorry, I encountered an error. Please try again."
            
            # Save bot response to Firebase for audit/compliance
            self._save_message(phone_number, "bot", response_text)
            
            return {"reply": response_text}
            
        except Exception as e:
            logger.error(f"Error processing cook message: {str(e)}")
            return {"reply": "I'm sorry, I encountered an error. Please try again."}

    def _get_or_create_session_id(self, phone_number: str) -> str:
        """Generate session ID for AgentCore memory (daily grouping)"""
        # Use phone_number + date as session ID
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{phone_number}_{date_str}"

    def _save_message(self, phone_number: str, role: str, content: str):
        """Save a message to the database"""
        try:
            message_data = {
                "role": role,
                "content": content
            }
            self.db.save_cook_message(phone_number, message_data)
        except Exception as e:
            logger.error(f"Error saving cook message: {str(e)}")


# Create singleton instance
cook_assistant_service = CookAssistantService()

