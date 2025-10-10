"""
Workflow module for BetterMeals WhatsApp agent.

This module provides structured onboarding flows for different types of users:
- Generic users: Standard onboarding flow
- Referral users: Special onboarding flow with discounts

The module is organized into separate files for better maintainability:
- base.py: Base classes and enums
- generic.py: Generic user onboarding flow
- referral.py: Referral user onboarding flow  
- service.py: Main service that routes to appropriate onboarding flow
"""

from .base import WorkflowStep, BaseWorkflow
from .generic import GenericChatWorkflow
from .service import WorkflowService, workflow_service

__all__ = [
    "WorkflowStep",
    "BaseWorkflow", 
    "GenericChatWorkflow",
    "WorkflowService",
    "workflow_service"
]
