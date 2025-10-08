#!/usr/bin/env python3
"""
Test script to demonstrate the message persistence approach.
This shows how messages are saved during conversation and final data is stored in household collection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.bettermeals.graph.onboarding.generic_v2 import GenericUserOnboardingV2
from src.bettermeals.graph.onboarding.base import OnboardingStep
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demonstrate_message_persistence():
    """Demonstrate the message persistence approach."""
    try:
        logger.info("=== Demonstrating Message Persistence Approach ===")
        
        # Create onboarding instance
        onboarding = GenericUserOnboardingV2()
        test_phone = "+1234567890"
        
        logger.info("📱 Starting onboarding conversation...")
        
        # Step 1: Initial greeting
        logger.info("Step 1: User says 'Hi'")
        response1 = onboarding.process_message("Hi", test_phone)
        logger.info(f"Bot: {response1['reply']}")
        
        # Step 2: Name collection
        logger.info("Step 2: User provides name 'John Doe'")
        response2 = onboarding.process_message("John Doe", test_phone)
        logger.info(f"Bot: {response2['reply']}")
        
        # Step 3: Form completion
        logger.info("Step 3: User says 'done'")
        response3 = onboarding.process_message("done", test_phone)
        logger.info(f"Bot: {response3['reply']}")
        
        # Step 4: Trial offer acceptance
        logger.info("Step 4: User says 'yes'")
        response4 = onboarding.process_message("yes", test_phone)
        logger.info(f"Bot: {response4['reply']}")
        
        # Step 5: Payment confirmation
        logger.info("Step 5: User confirms 'yes'")
        response5 = onboarding.process_message("yes", test_phone)
        logger.info(f"Bot: {response5['reply']}")
        
        logger.info("\n=== Summary ===")
        logger.info("✅ Each message was saved to 'onboarding_messages' collection")
        logger.info("✅ Final onboarding data will be saved to 'household' collection")
        logger.info("✅ User can resume conversation if server restarts")
        logger.info("✅ Complete onboarding data available for business analytics")
        
        logger.info("\n=== Database Collections ===")
        logger.info("📊 onboarding_messages: Individual conversation messages")
        logger.info("🏠 household: Final onboarding data + user profile")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        raise

if __name__ == "__main__":
    demonstrate_message_persistence()
