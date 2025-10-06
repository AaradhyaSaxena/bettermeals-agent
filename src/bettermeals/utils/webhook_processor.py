from typing import Dict, Any, Optional


class WebhookProcessor:
    """Helper class for processing WhatsApp webhook requests."""
    
    @staticmethod
    def extract_payload_data(payload: Dict[str, Any]) -> tuple[str, str, str]:
        """Extract and normalize data from the webhook payload."""
        text = payload.get("text", "")
        household_id = payload.get("thread_id") or payload.get("household_id", "demo_household")
        sender_role = payload.get("sender_role", "user")
        return text, household_id, sender_role

    @staticmethod
    def build_graph_input(text: str, household_id: str, sender_role: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Build the input state and configuration for the graph."""
        config = {"configurable": {"thread_id": household_id}}
        state_in = {
            "messages": [{"role": "user", "content": text}],
            "household_id": household_id,
            "sender_role": sender_role,
        }
        return state_in, config

    @staticmethod
    def debug_print_messages(messages: list) -> None:
        """Print debug information about all messages in the conversation."""
        print("=== DEBUG: All Messages ===")
        for i, msg in enumerate(messages):
            print(f"Message {i}: {type(msg).__name__}")
            if hasattr(msg, 'name'):
                print(f"  Name: {msg.name}")
            if hasattr(msg, 'content'):
                print(f"  Content: {msg.content[:100]}...")
            if hasattr(msg, 'tool_calls'):
                print(f"  Tool calls: {msg.tool_calls}")
            print("---")

    @staticmethod
    def extract_last_ai_message(messages: list) -> Optional[str]:
        """Extract the last AI-generated message from the conversation."""
        for msg in reversed(messages):
            # Handle LangChain message objects
            if hasattr(msg, 'content') and msg.content:
                # Check if it's an AI message (not from user)
                if hasattr(msg, 'name') and msg.name != 'user':
                    return msg.content
                elif hasattr(msg, '__class__') and 'AI' in msg.__class__.__name__:
                    return msg.content
        return None

    @staticmethod
    def build_response(last_message: Optional[str], final_state: Dict[str, Any]) -> Dict[str, Any]:
        """Build the final response object."""
        response = {"reply": last_message or "I'm processing your request..."}
        
        # Include pending action if present (for human-in-the-loop)
        if final_state.get("pending_action"):
            response["pending_action"] = final_state["pending_action"]
        
        return response
