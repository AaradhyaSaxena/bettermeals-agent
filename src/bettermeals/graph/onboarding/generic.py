from typing import Dict, Any
import logging

from .base import BaseOnboarding, OnboardingStep

# Configure logging
logger = logging.getLogger(__name__)


class GenericUserOnboarding(BaseOnboarding):
    """Onboarding flow for generic users"""
    
    def get_onboarding_type(self) -> str:
        return "generic"
    
    def _initialize_steps(self) -> Dict[OnboardingStep, callable]:
        return {
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
        
        self._set_onboarding_step(phone_number, OnboardingStep.NEEDS_ASSESSMENT)
        return {
            "reply": f"Nice to meet you, {name}! What are you looking for from BetterMeals?\n\n1. Convenience (menu planning, cook coordination, grocery ordering)\n2. Healthier meals\n3. Savings on groceries\n4. Save time\n5. Anything else?"
        }
    
    def _handle_needs_assessment(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle needs assessment step."""
        # Store the user's needs
        user_data = self._get_user_data(phone_number)
        user_data["needs"] = text
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.STRESS_POINTS)
        return {
            "reply": "Got it! Can you share what's most stressful for you—menu planning, cook coordination, or grocery shopping?"
        }
    
    def _handle_stress_points(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle stress points assessment."""
        # Store stress points
        user_data = self._get_user_data(phone_number)
        user_data["stress_points"] = text
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.COOK_COORDINATION_DETAILS)
        return {
            "reply": "Totally get you! What's tricky about coordinating with your cook? Timing, menu confusion, or something else?"
        }
    
    def _handle_cook_coordination_details(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle cook coordination details."""
        # Store cook coordination details
        user_data = self._get_user_data(phone_number)
        user_data["cook_coordination_details"] = text
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.COOK_STATUS)
        return {
            "reply": "You're not alone, yaar! BetterMeals sends your cook clear voice notes and step-by-step instructions on WhatsApp, so no more repeating yourself or recipe confusion. 😊\n\nDo you have a cook at home right now?"
        }
    
    def _handle_cook_status(self, text: str, phone_number: str) -> Dict[str, Any]:
        """Handle cook status question."""
        has_cook = text.lower().strip() in ["yes", "y", "yeah", "yep"]
        
        # Store cook status
        user_data = self._get_user_data(phone_number)
        user_data["has_cook"] = has_cook
        self._set_user_data(phone_number, user_data)
        
        self._set_onboarding_step(phone_number, OnboardingStep.TRIAL_OFFER)
        
        user_name = user_data.get("name", "there")
        
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
        
        self._set_onboarding_step(phone_number, OnboardingStep.GROUP_INVITATION)
        user_data = self._get_user_data(phone_number)
        user_name = user_data.get("name", "there")
        
        # Generate payment link (in production, integrate with payment gateway)
        upi_id = "9639293454@ybl"  # Mock id
        
        return {
            "reply": f"You can pay for the ₹49 trial at this UPI ID: {upi_id}\n\nLet me know once you've paid, {user_name}! 😊"
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
            user_data = self._get_user_data(phone_number)
            logger.info(f"Creating user record for {phone_number} with data: {user_data}")
            
            # In production, implement actual database creation
            # For now, just log the completion
            logger.info(f"Generic onboarding completed for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error creating user record for {phone_number}: {str(e)}")
