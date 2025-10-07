import pytest
from unittest.mock import patch, MagicMock
from src.bettermeals.graph.onboarding import OnboardingService, OnboardingStep


class TestOnboardingFlow:
    """Test the structured onboarding flow"""

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
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_name_collection_step(self):
        """Test name collection step"""
        # First set the step to name collection
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Shiwani"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Nice to meet you, Shiwani!" in response["reply"]
        assert "What are you looking for from BetterMeals?" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NEEDS_ASSESSMENT
        
        # Check that name was stored
        assert self.onboarding_service._user_data[self.test_phone]["name"] == "Shiwani"

    def test_needs_assessment_step(self):
        """Test needs assessment step"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.NEEDS_ASSESSMENT)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "1. 2. 4."
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Got it!" in response["reply"]
        assert "stressful for you" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.STRESS_POINTS

    def test_stress_points_step(self):
        """Test stress points assessment"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.STRESS_POINTS)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Cook coordination - most stressful"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Totally get you!" in response["reply"]
        assert "tricky about coordinating" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COOK_COORDINATION_DETAILS

    def test_cook_coordination_details_step(self):
        """Test cook coordination details step"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.COOK_COORDINATION_DETAILS)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Timing and explaining the nuances of a dish"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "You're not alone, yaar!" in response["reply"]
        assert "Do you have a cook at home right now?" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COOK_STATUS

    def test_cook_status_step_with_cook(self):
        """Test cook status step when user has a cook"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.COOK_STATUS)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Perfect!" in response["reply"]
        assert "₹49" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    def test_cook_status_step_without_cook(self):
        """Test cook status step when user doesn't have a cook"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.COOK_STATUS)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
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
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    def test_trial_offer_acceptance(self):
        """Test trial offer acceptance"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Sure"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Awesome!" in response["reply"]
        assert "confirm your name" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.PAYMENT_CONFIRMATION

    def test_payment_confirmation(self):
        """Test payment confirmation step"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.PAYMENT_CONFIRMATION)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Yes"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "UPI ID" in response["reply"]
        assert "9639293454@ybl" in response["reply"]
        
        # Check that step was updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.GROUP_INVITATION

    def test_group_invitation_after_payment(self):
        """Test group invitation after payment confirmation"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.GROUP_INVITATION)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Done ✅"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "WhatsApp group" in response["reply"]
        assert "join the group" in response["reply"]
        
        # Check that step was updated to completed
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.COMPLETED

    def test_empty_name_handling(self):
        """Test handling of empty name input"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.NAME_COLLECTION)
        
        payload = {
            "phone_number": self.test_phone,
            "text": ""
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "Please tell me your name" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.NAME_COLLECTION

    def test_trial_offer_rejection(self):
        """Test trial offer rejection"""
        # Set up previous step data
        self.onboarding_service._set_onboarding_step(self.test_phone, OnboardingStep.TRIAL_OFFER)
        self.onboarding_service._user_data = {self.test_phone: {"name": "Shiwani"}}
        
        payload = {
            "phone_number": self.test_phone,
            "text": "Not now"
        }
        
        response = self.onboarding_service.process_onboarding_message(payload)
        
        assert "reply" in response
        assert "No worries!" in response["reply"]
        assert "Take your time" in response["reply"]
        
        # Check that step was not updated
        current_step = self.onboarding_service._get_current_onboarding_step(self.test_phone)
        assert current_step == OnboardingStep.TRIAL_OFFER

    @patch('src.bettermeals.graph.onboarding.get_db')
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

    @patch('src.bettermeals.graph.onboarding.get_db')
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


if __name__ == "__main__":
    pytest.main([__file__])
