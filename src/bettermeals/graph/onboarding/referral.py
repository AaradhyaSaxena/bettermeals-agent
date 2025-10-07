from typing import Dict, Any
import logging

from .base import BaseOnboarding, OnboardingStep

# Configure logging
logger = logging.getLogger(__name__)


class ReferralUserOnboarding(BaseOnboarding):
    """Onboarding flow for referral users"""
    
    def get_onboarding_type(self) -> str:
        return "referral"
    
    def _initialize_steps(self) -> Dict[OnboardingStep, callable]:
        return {
            OnboardingStep.GREETING: self._handle_greeting,
            OnboardingStep.NAME_COLLECTION: self._handle_name_collection,
            OnboardingStep.NEEDS_ASSESSMENT: self._handle_treatment_plan,
            OnboardingStep.TRIAL_OFFER: self._handle_trial_offer,
            OnboardingStep.PAYMENT_CONFIRMATION: self._handle_payment_confirmation,
            OnboardingStep.GROUP_INVITATION: self._handle_group_invitation,
        }
    
    def _handle_greeting(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle initial greeting step for referral users."""
        self._set_onboarding_step(phone_number, OnboardingStep.NAME_COLLECTION)
        return {
            "reply": "Hey! I'm Zuko from Bettermeals. I see you were referred by Super Health hospital! May I know your name?"
        }
    
    def _handle_name_collection(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle name collection step for referral users."""
        name = text.strip()
        if not name:
            return {"reply": "Please tell me your name so I can help you better!"}
        
        # Store the name
        user_data = self._get_user_data(phone_number)
        user_data["name"] = name
        user_data["is_referral"] = True
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.NEEDS_ASSESSMENT)
        return {
            "reply": f"Nice to meet you, {name}! Since you were referred by Super Health hospital, you get a special discount! Which treatment plan are you looking for?\n\n1. Diabetes Management\n2. Heart Health\n3. Weight Management\n4. General Wellness\n5. Post-Surgery Recovery\n6. Other specific condition"
        }
    
    def _handle_treatment_plan(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle treatment plan selection for hospital referral users."""
        # Store the treatment plan
        user_data = self._get_user_data(phone_number)
        user_data["treatment_plan"] = text
        user_data["referral_source"] = "Super Health Hospital"
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.TRIAL_OFFER)
        user_name = user_data.get("name", "there")
        
        return {
            "reply": f"Perfect! BetterMeals will create personalized meal plans for your {text.lower()} needs. Since you were referred by Super Health hospital, you get the first month for just ₹299 instead of ₹499!"
        }
    
    
    
    def _handle_trial_offer(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle trial offer acceptance for referral users."""
        accepted = text.lower().strip() in ["sure", "yes", "y", "yeah", "yep", "ok", "okay"]
        
        if not accepted:
            return {
                "reply": "No worries! Take your time. Feel free to reach out when you're ready to try BetterMeals with Super Health hospital's special pricing."
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.PAYMENT_CONFIRMATION)
        user_data = self._get_user_data(phone_number)
        user_name = user_data.get("name", "there")
        
        return {
            "reply": f"Awesome! Can you confirm your name for the payment link? Is it {user_name}?"
        }
    
    def _handle_payment_confirmation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle payment confirmation for referral users."""
        confirmed = text.lower().strip() in ["yes", "y", "yeah", "yep"]
        
        if not confirmed:
            return {
                "reply": "Please confirm your name so I send you the payment details"
            }
        
        self._set_onboarding_step(phone_number, OnboardingStep.GROUP_INVITATION)
        user_data = self._get_user_data(phone_number)
        user_name = user_data.get("name", "there")
        
        # Generate payment link for referral users (special discount)
        upi_id = "9639293454@ybl"  # Mock id
        
        return {
            "reply": f"Here's the UPI ID for the ₹299 trial (referral discount): {upi_id}\n\nLet me know once you've paid, {user_name}! 😊"
        }
    
    def _handle_group_invitation(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle group invitation after payment for referral users."""
        if "done" in text.lower() or "✅" in text or "paid" in text.lower():
            self._set_onboarding_step(phone_number, OnboardingStep.COMPLETED)
            
            # In production, create user record and household in database
            self._create_user_record(phone_number)
            
            return {
                "reply": "You have received the invite for WhatsApp group. Please join the group and our team will lead you from there. Thanks for joining through Super Health hospital referral!"
            }
        else:
            return {
                "reply": "Please let me know once you've completed the payment so I can send you the group invitation."
            }
    
    def _create_user_record(self, phone_number: str):
        """Create user record in database after successful referral onboarding."""
        try:
            user_data = self._get_user_data(phone_number)
            logger.info(f"Creating referral user record for {phone_number} with data: {user_data}")
            
            # In production, implement actual database creation
            # For now, just log the completion
            logger.info(f"Super Health hospital referral onboarding completed for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error creating referral user record for {phone_number}: {str(e)}")
