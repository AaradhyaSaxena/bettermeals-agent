from typing import Dict, Any, Optional, Tuple
import logging
from enum import Enum

from src.bettermeals.database.database import get_db

# Configure logging
logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Enumeration of onboarding steps"""
    GREETING = "greeting"
    NAME_COLLECTION = "name_collection"
    NEEDS_ASSESSMENT = "needs_assessment"
    STRESS_POINTS = "stress_points"
    COOK_COORDINATION_DETAILS = "cook_coordination_details"
    COOK_STATUS = "cook_status"
    TRIAL_OFFER = "trial_offer"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    GROUP_INVITATION = "group_invitation"
    COMPLETED = "completed"


class OnboardingService:
    """Service to onboard new users with structured flow"""

    def __init__(self):
        self.onboarding_steps = {
            OnboardingStep.GREETING: self._handle_greeting,
            OnboardingStep.NAME_COLLECTION: self._handle_name_collection,
            OnboardingStep.NEEDS_ASSESSMENT: self._handle_needs_assessment,
            OnboardingStep.STRESS_POINTS: self._handle_stress_points,
            OnboardingStep.COOK_COORDINATION_DETAILS: self._handle_cook_coordination_details,
            OnboardingStep.COOK_STATUS: self._handle_cook_status,
            OnboardingStep.TRIAL_OFFER: self._handle_trial_offer,
            OnboardingStep.PAYMENT_CONFIRMATION: self._handle_payment_confirmation,
            OnboardingStep.GROUP_INVITATION: self._handle_group_invitation,
        }

    def check_if_onboarded(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
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

    def process_onboarding_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process onboarding message and return appropriate response."""
        try:
            phone_number = payload.get("phone_number")
            text = payload.get("text", "").strip()
            
            # Get current onboarding state for this user
            current_step = self._get_current_onboarding_step(phone_number)
            logger.info(f"Processing onboarding for {phone_number} at step: {current_step}")
            
            # Process the current step
            if current_step in self.onboarding_steps:
                response = self.onboarding_steps[current_step](text, phone_number)
                return response
            else:
                # Default fallback
                return {"reply": "Welcome to Bettermeals! Let's get started. What's your name?"}
                
        except Exception as e:
            logger.error(f"Error processing onboarding message: {str(e)}")
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

    def _handle_greeting(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle initial greeting step."""
        self._set_onboarding_step(phone_number, OnboardingStep.NAME_COLLECTION)
        return {
            "reply": "Hey! I'm Zuko from Bettermeals. May I know your name?"
        }

    def _handle_name_collection(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle name collection step."""
        name = text.strip()
        if not name:
            return {"reply": "Please tell me your name so I can help you better!"}
        
        # Store the name (in production, save to database)
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        self._user_data[phone_number] = {"name": name}
        
        self._set_onboarding_step(phone_number, OnboardingStep.NEEDS_ASSESSMENT)
        return {
            "reply": f"Nice to meet you, {name}! What are you looking for from BetterMeals?\n\n1. Convenience (menu planning, cook coordination, grocery ordering)\n2. Healthier meals\n3. Savings on groceries\n4. Save time\n5. Anything else?"
        }

    def _handle_needs_assessment(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle needs assessment step."""
        # Store the user's needs
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        if phone_number not in self._user_data:
            self._user_data[phone_number] = {}
        self._user_data[phone_number]["needs"] = text
        
        self._set_onboarding_step(phone_number, OnboardingStep.STRESS_POINTS)
        return {
            "reply": "Got it! Can you share what's most stressful for you—menu planning, cook coordination, or grocery shopping?"
        }

    def _handle_stress_points(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle stress points assessment."""
        # Store stress points
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        if phone_number not in self._user_data:
            self._user_data[phone_number] = {}
        self._user_data[phone_number]["stress_points"] = text
        
        self._set_onboarding_step(phone_number, OnboardingStep.COOK_COORDINATION_DETAILS)
        return {
            "reply": "Totally get you! What's tricky about coordinating with your cook? Timing, menu confusion, or something else?"
        }

    def _handle_cook_coordination_details(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle cook coordination details."""
        # Store cook coordination details
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        if phone_number not in self._user_data:
            self._user_data[phone_number] = {}
        self._user_data[phone_number]["cook_coordination_details"] = text
        
        self._set_onboarding_step(phone_number, OnboardingStep.COOK_STATUS)
        return {
            "reply": "You're not alone, yaar! BetterMeals sends your cook clear voice notes and step-by-step instructions on WhatsApp, so no more repeating yourself or recipe confusion. 😊\n\nDo you have a cook at home right now?"
        }

    def _handle_cook_status(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle cook status question."""
        has_cook = text.lower().strip() in ["yes", "y", "yeah", "yep"]
        
        # Store cook status
        if not hasattr(self, '_user_data'):
            self._user_data = {}
        if phone_number not in self._user_data:
            self._user_data[phone_number] = {}
        self._user_data[phone_number]["has_cook"] = has_cook
        
        self._set_onboarding_step(phone_number, OnboardingStep.TRIAL_OFFER)
        
        user_name = self._user_data.get(phone_number, {}).get("name", "there")
        
        if has_cook:
            return {
                "reply": f"Perfect! BetterMeals will help coordinate with your cook seamlessly. Want to try it for a month at just ₹49?"
            }
        else:
            return {
                "reply": f"Thanks for sharing, {user_name}! Even without a cook, BetterMeals can plan your meals, suggest groceries, and save you time. Want to try it for a month at just ₹49?"
            }

    def _handle_trial_offer(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle trial offer acceptance."""
        accepted = text.lower().strip() in ["sure", "yes", "y", "yeah", "yep", "ok", "okay"]
        
        if not accepted:
            return {
                "reply": "No worries! Take your time. Feel free to reach out when you're ready to try BetterMeals."
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.PAYMENT_CONFIRMATION)
        user_name = self._user_data.get(phone_number, {}).get("name", "there")
        
        return {
            "reply": f"Awesome! Can you confirm your name for the payment link? Is it {user_name}?"
        }

    def _handle_payment_confirmation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle payment confirmation."""
        confirmed = text.lower().strip() in ["yes", "y", "yeah", "yep"]
        
        if not confirmed:
            return {
                "reply": "Please confirm your name so I send you the payment details"
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.GROUP_INVITATION)
        user_name = self._user_data.get(phone_number, {}).get("name", "there")
        
        # Generate payment link (in production, integrate with payment gateway)
        upi_id = "9639293454@ybl"  # Mock id
        
        return {
            "reply": f"Here's the UPI ID for the ₹49 trial: {upi_id}\n\nLet me know once you've paid, {user_name}! 😊"
        }

    def _handle_group_invitation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle group invitation after payment."""
        if "done" in text.lower() or "✅" in text or "paid" in text.lower():
            self._set_onboarding_step(phone_number, OnboardingStep.COMPLETED)
            
            # In production, create user record and household in database
            self._create_user_record(phone_number)
            
            return {
                "reply": "You have received the invite for WhatsApp group. Please join the group and our team will lead you from there."
            }
        else:
            return {
                "reply": "Please let me know once you've completed the payment so I can send you the group invitation."
            }

    def _create_user_record(self, phone_number: str):
        """Create user record in database after successful onboarding."""
        try:
            user_data = self._user_data.get(phone_number, {})
            logger.info(f"Creating user record for {phone_number} with data: {user_data}")
            
            # In production, implement actual database creation
            # For now, just log the completion
            logger.info(f"Onboarding completed for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error creating user record for {phone_number}: {str(e)}")


onboarding_service = OnboardingService()
