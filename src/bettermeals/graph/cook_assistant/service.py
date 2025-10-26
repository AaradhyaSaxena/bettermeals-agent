from typing import Dict, Any, Optional, List
import logging
import asyncio
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

    def process_cook_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process cook assistant message and return appropriate response"""
        try:
            phone_number = payload.get("phone_number")
            text = payload.get("text", "").strip()
            
            if not phone_number or not text:
                return {"reply": "I need your message to help you. What would you like to know?"}
            
            logger.info(f"Processing cook message from {phone_number}: {text}")
            
            # Save user message
            self._save_message(phone_number, "user", text)
            
            # Get conversation history
            conversation_history = self._get_conversation_history(phone_number)
            
            # Invoke bedrock agent
            try:
                response_text = asyncio.run(invoke_cook_assistant(text, conversation_history))
            except Exception as e:
                logger.error(f"Error invoking bedrock agent: {str(e)}")
                response_text = "I'm sorry, I encountered an error. Please try again."
            
            # Save bot response
            self._save_message(phone_number, "bot", response_text)
            
            return {"reply": response_text}
            
        except Exception as e:
            logger.error(f"Error processing cook message: {str(e)}")
            return {"reply": "I'm sorry, I encountered an error. Please try again."}

    def _get_conversation_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for context"""
        try:
            messages = self.db.get_cook_messages(phone_number, limit)
            
            # Format as conversation history (exclude the current message being processed)
            history = []
            for msg in messages[:-1]:  # Exclude last message (current user message)
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:  # Only add non-empty messages
                    history.append({"role": role, "content": content})
            
            return history
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

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

