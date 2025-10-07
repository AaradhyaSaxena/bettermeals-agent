import pytest
from unittest.mock import patch, MagicMock
from src.bettermeals.graph.onboarding import OnboardingService, OnboardingStep, GenericUserOnboarding, ReferralUserOnboarding


class TestGenericOnboardingFlow:
    """Test the structured onboarding flow for generic users"""

    def setup_method(self):
        """Set up test fixtures"""
        self.onboarding_service = OnboardingService()
        self.test_phone = "+1234567890"

    def test_greeting_step(self):
        """Test the initial greeting step"""
        payload = {
            "phone_number": self.test_phone,
            "text": "Hi"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Zuko from Bettermeals" in response["reply"]
        assert "May I know your name" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_name_collection_step(self):
        """Test name collection step"""
        # First set the step to name collection
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Shiwani"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Nice to meet you, Shiwani!" in response["reply"]
        assert "What are you looking for from BetterMeals?" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NEEDS_ASSESSMENT
        
        # Check that name was stored
        assert self.onboarding_service.generic_onboarding._get_user_data(self.test_phone)["name"] == "Shiwani"

    def test_needs_assessment_step(self):
        """Test needs assessment step"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "1. 2. 4."
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Got it!" in response["reply"]
        assert "stressful for you" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.STRESS_POINTS

    def test_stress_points_step(self):
        """Test stress points assessment"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.STRESS_POINTS)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Cook coordination - most stressful"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Totally get you!" in response["reply"]
        assert "tricky about coordinating" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COOK_COORDINATION_DETAILS

    def test_cook_coordination_details_step(self):
        """Test cook coordination details step"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.COOK_COORDINATION_DETAILS)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Timing and explaining the nuances of a dish"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "You're not alone, yaar!" in response["reply"]
        assert "Do you have a cook at home right now?" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COOK_STATUS

    def test_cook_status_step_with_cook(self):
        """Test cook status step when user has a cook"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.COOK_STATUS)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Perfect!" in response["reply"]
        assert "₹49" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    def test_cook_status_step_without_cook(self):
        """Test cook status step when user doesn't have a cook"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.COOK_STATUS)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "No"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Thanks for sharing, Shiwani!" in response["reply"]
        assert "Even without a cook" in response["reply"]
        assert "₹49" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    def test_trial_offer_acceptance(self):
        """Test trial offer acceptance"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Sure"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Awesome!" in response["reply"]
        assert "confirm your name" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.PAYMENT_CONFIRMATION

    def test_payment_confirmation(self):
        """Test payment confirmation step"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.PAYMENT_CONFIRMATION)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "UPI ID" in response["reply"]
        assert "9639293454@ybl" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.GROUP_INVITATION

    def test_group_invitation_after_payment(self):
        """Test group invitation after payment confirmation"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.GROUP_INVITATION)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Done ✅"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "WhatsApp group" in response["reply"]
        assert "join the group" in response["reply"]
        
        # Check that step was updated to completed
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COMPLETED

    def test_empty_name_handling(self):
        """Test handling of empty name input"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": ""
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Please tell me your name" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_trial_offer_rejection(self):
        """Test trial offer rejection"""
        # Set up previous step data
        self.onboarding_service.generic_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service.generic_onboarding._set_user_data(self.test_phone, {"name": "Shiwani"})
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Not now"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "No worries!" in response["reply"]
        assert "Take your time" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.generic_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    @patch('src.bettermeals.graph.onboarding.service.get_db')
    def test_check_if_onboarded_existing_user(self, mock_get_db):
        """Test checking onboarding status for existing user"""
        # Mock database response
        mock_db = MagicMock()
        mock_user = {"id": "user123", "householdId": "household123"}
        mock_household = {"id": "household123", "name": "Test Household"}
        
        mock_db.find_user_by_phone.return_value = mock_user
        mock_db.get_household_data.return_value = mock_household
        mock_get_db.return_value = mock_db
        
        payload = {"phone_number": self.test_phone}
        
        is_onboarded, household_data = self.onboarding_service.check_if_onboarded(payload)
        
        assert is_onboarded is True
        assert household_data == mock_household
        mock_db.find_user_by_phone.assert_called_once_with(self.test_phone)
        mock_db.get_household_data.assert_called_once_with("household123")

    @patch('src.bettermeals.graph.onboarding.service.get_db')
    def test_check_if_onboarded_new_user(self, mock_get_db):
        """Test checking onboarding status for new user"""
        # Mock database response - no user found
        mock_db = MagicMock()
        mock_db.find_user_by_phone.return_value = None
        mock_get_db.return_value = mock_db
        
        payload = {"phone_number": self.test_phone}
        
        is_onboarded, household_data = self.onboarding_service.check_if_onboarded(payload)
        
        assert is_onboarded is False
        assert household_data is None
        mock_db.find_user_by_phone.assert_called_once_with(self.test_phone)
        mock_db.get_household_data.assert_not_called()


class TestReferralOnboardingFlow:
    """Test the structured onboarding flow for hospital referral users"""

    def setup_method(self):
        """Set up test fixtures"""
        self.onboarding_service = OnboardingService()
        self.test_phone = "+9876543210"

    def test_referral_greeting_step(self):
        """Test the initial greeting step for hospital referrals"""
        payload = {
            "phone_number": self.test_phone,
            "text": "Hi",
            "referral_code": "super_health_123"  # This triggers referral flow
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Zuko from Bettermeals" in response["reply"]
        assert "Super Health hospital" in response["reply"]
        assert "May I know your name" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_referral_name_collection_step(self):
        """Test name collection step for hospital referrals"""
        # First set the step to name collection
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Dr. Mira",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Nice to meet you, Dr. Mira!" in response["reply"]
        assert "Super Health hospital" in response["reply"]
        assert "special discount" in response["reply"]
        assert "treatment plan" in response["reply"]
        assert "Diabetes Management" in response["reply"]
        assert "Heart Health" in response["reply"]
        assert "Weight Management" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NEEDS_ASSESSMENT
        
        # Check that name and referral status were stored
        user_data = self.onboarding_service.referral_onboarding._get_user_data(self.test_phone)
        assert user_data["name"] == "Dr. Mira"
        assert user_data["is_referral"] is True

    def test_treatment_plan_selection_diabetes(self):
        """Test treatment plan selection for diabetes management"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Diabetes Management",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Perfect!" in response["reply"]
        assert "diabetes management needs" in response["reply"]
        assert "Super Health hospital" in response["reply"]
        assert "₹299 instead of ₹499" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER
        
        # Check that treatment plan was stored
        user_data = self.onboarding_service.referral_onboarding._get_user_data(self.test_phone)
        assert user_data["treatment_plan"] == "Diabetes Management"
        assert user_data["referral_source"] == "Super Health Hospital"

    def test_treatment_plan_selection_heart_health(self):
        """Test treatment plan selection for heart health"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Heart Health",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "heart health needs" in response["reply"]
        assert "₹299 instead of ₹499" in response["reply"]
        
        # Check that treatment plan was stored
        user_data = self.onboarding_service.referral_onboarding._get_user_data(self.test_phone)
        assert user_data["treatment_plan"] == "Heart Health"

    def test_treatment_plan_selection_weight_management(self):
        """Test treatment plan selection for weight management"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Weight Management",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "weight management needs" in response["reply"]
        assert "₹299 instead of ₹499" in response["reply"]

    def test_treatment_plan_selection_post_surgery(self):
        """Test treatment plan selection for post-surgery recovery"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Post-Surgery Recovery",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "post-surgery recovery needs" in response["reply"]
        assert "₹299 instead of ₹499" in response["reply"]

    def test_referral_trial_offer_acceptance(self):
        """Test trial offer acceptance for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True,
            "treatment_plan": "Diabetes Management",
            "referral_source": "Super Health Hospital"
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Awesome!" in response["reply"]
        assert "confirm your name" in response["reply"]
        assert "Dr. Mira" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.PAYMENT_CONFIRMATION

    def test_referral_trial_offer_rejection(self):
        """Test trial offer rejection for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True,
            "treatment_plan": "Diabetes Management"
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Not right now",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "No worries!" in response["reply"]
        assert "Super Health hospital's special pricing" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    def test_referral_payment_confirmation(self):
        """Test payment confirmation for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.PAYMENT_CONFIRMATION)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True,
            "treatment_plan": "Diabetes Management",
            "referral_source": "Super Health Hospital"
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "UPI ID" in response["reply"]
        assert "9639293454@ybl" in response["reply"]
        assert "₹299 trial (referral discount)" in response["reply"]
        assert "Dr. Mira" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.GROUP_INVITATION

    def test_referral_payment_confirmation_rejection(self):
        """Test payment confirmation rejection for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.PAYMENT_CONFIRMATION)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "No, that's not right",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Please confirm your name" in response["reply"]
        assert "payment details" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.PAYMENT_CONFIRMATION

    def test_referral_group_invitation_after_payment(self):
        """Test group invitation after payment for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.GROUP_INVITATION)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True,
            "treatment_plan": "Diabetes Management",
            "referral_source": "Super Health Hospital"
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Done ✅",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "WhatsApp group" in response["reply"]
        assert "join the group" in response["reply"]
        assert "Super Health hospital referral" in response["reply"]
        
        # Check that step was updated to completed
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COMPLETED

    def test_referral_group_invitation_pending_payment(self):
        """Test group invitation when payment is still pending for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.GROUP_INVITATION)
        self.onboarding_service.referral_onboarding._set_user_data(self.test_phone, {
            "name": "Dr. Mira",
            "is_referral": True
        })
        
        payload = {
            "phone_number": self.test_phone,
            "text": "I'm still working on it",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "completed the payment" in response["reply"]
        assert "group invitation" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.GROUP_INVITATION

    def test_referral_empty_name_handling(self):
        """Test handling of empty name input for hospital referrals"""
        # Set up previous step data
        self.onboarding_service.referral_onboarding._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": "",
            "referral_code": "super_health_123"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Please tell me your name" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_referral_onboarding_type_detection(self):
        """Test that referral onboarding type is correctly detected"""
        assert self.onboarding_service.referral_onboarding.get_onboarding_type() == "referral"

    def test_referral_vs_generic_routing(self):
        """Test that referral code triggers referral flow vs generic flow"""
        # Test with referral code - should use referral onboarding
        payload_with_referral = {
            "phone_number": self.test_phone,
            "text": "Hi",
            "referral_code": "super_health_123"
        }
        
        response_referral = self.onboarding_service.process_onboarding_message(payload_with_referral)
        assert "Super Health hospital" in response_referral["reply"]
        
        # Test without referral code - should use generic onboarding
        payload_without_referral = {
            "phone_number": "+1111111111",  # Different phone to avoid state conflicts
            "text": "Hi"
        }
        
        response_generic = self.onboarding_service.process_onboarding_message(payload_without_referral)
        assert "Super Health hospital" not in response_generic["reply"]
        assert "May I know your name" in response_generic["reply"]

    def test_referral_complete_flow_integration(self):
        """Test complete referral onboarding flow from start to finish"""
        phone = "+5555555555"
        
        # Step 1: Greeting
        response1 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Hello",
            "referral_code": "super_health_123"
        })
        assert "Super Health hospital" in response1["reply"]
        
        # Step 2: Name collection
        response2 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Dr. Michael Chen",
            "referral_code": "super_health_123"
        })
        assert "Dr. Michael Chen" in response2["reply"]
        assert "treatment plan" in response2["reply"]
        
        # Step 3: Treatment plan
        response3 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Heart Health",
            "referral_code": "super_health_123"
        })
        assert "heart health needs" in response3["reply"]
        assert "₹299 instead of ₹499" in response3["reply"]
        
        # Step 4: Trial offer acceptance
        response4 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Yes",
            "referral_code": "super_health_123"
        })
        assert "confirm your name" in response4["reply"]
        
        # Step 5: Payment confirmation
        response5 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Yes",
            "referral_code": "super_health_123"
        })
        assert "₹299 trial (referral discount)" in response5["reply"]
        
        # Step 6: Payment completion
        response6 = self.onboarding_service.process_onboarding_message({
            "phone_number": phone,
            "text": "Paid ✅",
            "referral_code": "super_health_123"
        })
        assert "Super Health hospital referral" in response6["reply"]
        
        # Verify final state
        final_step = self.onboarding_service.referral_onboarding._get_current_onboarding_step(phone)
        assert final_step == OnboardingStep.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__])
