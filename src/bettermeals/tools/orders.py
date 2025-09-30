from langchain_core.tools import tool
from ..config.settings import settings
from .http_client import post_json, get_json
import uuid
from datetime import datetime, timedelta

@tool("bm_build_cart", description="Build cart from meal plan.")
async def bm_build_cart(household_id: str, meal_plan_id: str) -> dict:
    """Create a grocery cart from a meal plan."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/orders/build_cart",
    #                        {"household_id": household_id, "meal_plan_id": meal_plan_id})
    
    # Mock response for cart building
    cart_id = str(uuid.uuid4())
    return {
        "success": True,
        "cart_id": cart_id,
        "household_id": household_id,
        "meal_plan_id": meal_plan_id,
        "items": [
            {"name": "Chicken Breast", "quantity": "2 lbs", "price": 12.99},
            {"name": "Rice", "quantity": "1 bag", "price": 3.49},
            {"name": "Broccoli", "quantity": "1 head", "price": 2.99}
        ],
        "total": 19.47,
        "created_at": datetime.now().isoformat(),
        "message": "Cart built successfully from meal plan"
    }

@tool("bm_substitute", description="Propose or accept a substitution in cart.")
async def bm_substitute(cart_id: str, original: str, chosen: str) -> dict:
    """Update cart with a substitution selection."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/orders/substitute",
    #                        {"cart_id": cart_id, "original": original, "chosen": chosen})
    
    # Mock response for substitution
    return {
        "success": True,
        "cart_id": cart_id,
        "original": original,
        "chosen": chosen,
        "price_difference": 0.50,
        "updated_at": datetime.now().isoformat(),
        "message": f"Substituted {original} with {chosen}"
    }

@tool("bm_checkout", description="Checkout cart (idempotent).")
async def bm_checkout(cart_id: str, idempotency_key: str) -> dict:
    """Place the grocery order using an idempotency key to avoid duplicate charges."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/orders/checkout",
    #                        {"cart_id": cart_id, "idempotency_key": idempotency_key})
    
    # Mock response for checkout
    order_id = str(uuid.uuid4())
    return {
        "success": True,
        "order_id": order_id,
        "cart_id": cart_id,
        "idempotency_key": idempotency_key,
        "total": 19.47,
        "status": "created",
        "estimated_delivery": (datetime.now() + timedelta(days=2)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "message": "Order placed successfully"
    }

@tool("bm_order_status", description="Fetch order status by ID.")
async def bm_order_status(order_id: str) -> dict:
    """Get order status (created/packed/delivered) and ETA."""
    # TODO: Uncomment when API is working
    # return await get_json(f"{settings.bm_api_base}/orders/status", params={"order_id": order_id})
    
    # Mock response for order status
    return {
        "success": True,
        "order_id": order_id,
        "status": "packed",
        "progress": 75,
        "estimated_delivery": (datetime.now() + timedelta(hours=6)).isoformat(),
        "tracking_info": {
            "current_location": "Distribution Center",
            "next_update": (datetime.now() + timedelta(hours=2)).isoformat()
        },
        "last_updated": datetime.now().isoformat(),
        "message": "Order is packed and ready for delivery"
    }
