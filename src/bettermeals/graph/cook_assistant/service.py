from typing import Dict, Any
import logging
import hashlib
from datetime import datetime
from ...database.database import get_db
from .bedrock import invoke_cook_assistant

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
            # Ensures >= 33 characters for Bedrock Runtime API compatibility
            session_id = self._get_or_create_session_id(phone_number)
            
            # Build context dictionary with available values for tool calls
            # This is generic and extensible - add new keys as new tools/parameters are added
            context = self._build_tool_context(phone_number, payload)
            
            # Invoke bedrock agent with AgentCore memory and context
            try:
                response_text = await invoke_cook_assistant(
                    prompt=text,
                    actor_id=phone_number,
                    session_id=session_id,
                    context=context
                )
                response = self._format_msg_for_whatsapp(response_text)
            except Exception as e:
                logger.error(f"Error invoking bedrock agent: {str(e)}")
                response = "I'm sorry, I encountered an error. Please try again."
            
            # Save bot response to Firebase for audit/compliance
            self._save_message(phone_number, "bot", response)
            
            return {"reply": response}
            
        except Exception as e:
            logger.error(f"Error processing cook message: {str(e)}")
            return {"reply": "I'm sorry, I encountered an error. Please try again."}
    
    def _build_tool_context(self, phone_number: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a generic context dictionary with available values for tool calls.
        
        This method extracts context values from the database and payload.
        It's designed to be easily extensible - add new key-value pairs as needed
        when new tools or parameters are introduced.
        
        Args:
            phone_number: Cook's phone number
            payload: Request payload that may contain context values
            
        Returns:
            Dictionary of context key-value pairs (keys should match tool parameter names)
        """
        context = {}
        context["phone_number"] = phone_number
        
        # Extract cook_id from database
        cook_data = self.db.find_cook_by_phone(phone_number)
        if cook_data:
            cook_id = cook_data.get("id")
            if cook_id:
                context["cook_id"] = cook_id
            
            # Extract household_id from cook data if available
            household_id = cook_data.get("household_id")
            if household_id:
                context["household_id"] = household_id
        
        # Extract household_id from payload (takes precedence)
        if payload.get("household_id"):
            context["household_id"] = payload.get("household_id")
        
        # Extract meal_id from payload if present
        if payload.get("meal_id"):
            context["meal_id"] = payload.get("meal_id")
        
        # Calculate year_week in format "YYYY-Www" (e.g., "2024-W01")
        now = datetime.now()
        week_num = now.strftime("%W")
        context["year_week"] = f"{now.year}-{week_num}"
        
        return context

    def _get_or_create_session_id(self, phone_number: str) -> str:
        """
        Generate session ID for AgentCore memory (daily grouping).
        
        Bedrock Runtime API requires runtimeSessionId to be at least 33 characters.
        This method ensures the session ID meets that requirement while maintaining
        determinism (same phone_number + date = same session_id).
        """
        date_str = datetime.now().strftime("%Y%m%d")
        base_id = f"{phone_number}_{date_str}"
        
        # If already long enough, return as-is
        if len(base_id) >= 33:
            return base_id
        
        # Calculate padding needed: 33 - len(base_id) - 1 (for underscore)
        padding_needed = max(0, 33 - len(base_id) - 1)
        
        # Generate deterministic hash suffix (always use at least 16 chars for uniqueness)
        hash_digest = hashlib.sha256(base_id.encode()).hexdigest()
        hash_length = max(16, padding_needed)
        hash_suffix = hash_digest[:hash_length]
        
        return f"{base_id}_{hash_suffix}"

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

    def _format_msg_for_whatsapp(self, msg: str) -> str:
        """Format message for WhatsApp"""
        # Replace literal \n strings (from JSON-encoded responses) with \r for WhatsApp line breaks
        # Also handle actual newline characters as fallback
        return msg.replace("\\n", "\r").replace("\n", "\r")

# Create singleton instance
cook_assistant_service = CookAssistantService()

