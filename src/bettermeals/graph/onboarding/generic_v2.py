from typing import Dict, Any
import logging

from .base import BaseOnboarding, OnboardingStep

# Configure logging
logger = logging.getLogger(__name__)


class GenericUserOnboardingV2(BaseOnboarding):
    """Onboarding flow for generic users"""
    
    def get_onboarding_type(self) -> str:
        return "generic"
    
    def _initialize_steps(self) -> Dict[OnboardingStep, callable]:
        return {
            OnboardingStep.GREETING: self._handle_greeting,
            OnboardingStep.NAME_COLLECTION: self._handle_name_collection,
            OnboardingStep.FORM_COMPLETION: self._handle_form_completion,
            OnboardingStep.TRIAL_OFFER: self._handle_trial_offer,
            OnboardingStep.PAYMENT_CONFIRMATION: self._handle_payment_confirmation,
            # OnboardingStep.GROUP_INVITATION: self._handle_group_invitation,
        }
    
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
        
        # Store the name
        user_data = self._get_user_data(phone_number)
        user_data["name"] = name
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.FORM_COMPLETION)
        return {
            "reply": f"Nice to meet you, {name}! Please complete this quick onboarding form to get started: https://bettermeals.in/onboarding \n\n Let me know once you've completed the form!"
        }
    
    def _handle_form_completion(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle form completion step."""
        completion_keywords = ["done", "completed", "finished"]
        # Import locally to avoid circular import
        from .service import onboarding_service
        if any(keyword in text.lower() for keyword in completion_keywords) and onboarding_service.check_if_onboarded(phone_number)[0]:
            self._set_onboarding_step(phone_number, OnboardingStep.TRIAL_OFFER)
            user_data = self._get_user_data(phone_number)
            user_name = user_data.get("name", "there")
            return {
                "reply": f"Perfect, {user_name}! Thanks for completing the form. Want to try BetterMeals for a month at just ₹149?"
            }    
        else:
            return {
                "reply": "Please complete the onboarding form first: https://bettermeals.in/onboarding \n\nLet me know once you're done!"
            }
    
    def _handle_trial_offer(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle trial offer acceptance."""
        accepted = text.lower().strip() in ["sure", "yes", "y", "yeah", "yep", "ok", "okay"]
        
        if not accepted:
            return {
                "reply": "No worries! Take your time. Feel free to reach out when you're ready to try BetterMeals."
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.PAYMENT_CONFIRMATION)
        user_data = self._get_user_data(phone_number)
        user_name = user_data.get("name", "there")
        
        return {
            "reply": f"Awesome! Can you confirm your name for the payment link? Is it {user_name}?"
        }
    
    def _handle_payment_confirmation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle payment confirmation."""
        confirmed = text.lower().strip() in ["yes", "y", "yeah", "yep"]
        
        if not confirmed:
            return {
                "reply": "Please confirm your name once, before the payment process starts"
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.COMPLETED)
        # Save final onboarding data to household collection
        self._save_final_onboarding_data(phone_number)
        
        user_data = self._get_user_data(phone_number)
        user_name = user_data.get("name", "there")
        
        # Generate payment link (in production, integrate with payment gateway)
        upi_id = "9639293454@ybl"  # Mock id
        
        return {
            "reply": f"You can pay for the ₹149 trial at this UPI ID: {upi_id}\n\nLet me know once you've paid, {user_name}! 😊"
        }
    
    def _handle_group_invitation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle group invitation after payment."""
        if "done" in text.lower() or "✅" in text or "paid" in text.lower():
            self._set_onboarding_step(phone_number, OnboardingStep.COMPLETED)
            # Save final onboarding data to household collection
            self._save_final_onboarding_data(phone_number)
            
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
            user_data = self._get_user_data(phone_number)
            logger.info(f"Creating user record for {phone_number} with data: {user_data}")
            
            # In production, implement actual database creation
            # For now, just log the completion
            logger.info(f"Generic onboarding completed for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error creating user record for {phone_number}: {str(e)}")
