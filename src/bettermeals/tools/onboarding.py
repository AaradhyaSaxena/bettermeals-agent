from langchain_core.tools import tool
from ..config.settings import settings
from .http_client import post_json
import uuid
from datetime import datetime

@tool("bm_onboard_household", description="Create or update a household profile.")
async def bm_onboard_household(phone_hash: str, preferences: dict) -> dict:
    """Create/update household; preferences include veg/non-veg, allergies, constraints."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/onboarding/household",
    #                        {"phone_hash": phone_hash, "preferences": preferences})
    
    # Mock response for household onboarding
    household_id = str(uuid.uuid4())
    return {
        "success": True,
        "household_id": household_id,
        "phone_hash": phone_hash,
        "preferences": preferences,
        "created_at": datetime.now().isoformat(),
        "message": "Household profile created successfully"
    }

@tool("bm_onboard_resident", description="Create or update a resident profile.")
async def bm_onboard_resident(household_id: str, resident: dict) -> dict:
    """Create/update resident under a household."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/onboarding/resident",
    #                        {"household_id": household_id, "resident": resident})
    
    # Mock response for resident onboarding
    resident_id = str(uuid.uuid4())
    return {
        "success": True,
        "resident_id": resident_id,
        "household_id": household_id,
        "resident": resident,
        "created_at": datetime.now().isoformat(),
        "message": "Resident profile created successfully"
    }
