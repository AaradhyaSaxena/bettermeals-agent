from langchain_core.tools import tool
from ..config.settings import settings
from .http_client import post_json
import uuid
from datetime import datetime, timedelta

@tool("bm_recommend_meals", description="Call BetterMeals recommendations API.")
async def bm_recommend_meals(
    household_id: str, 
    constraints: dict = {}
) -> dict:
    """Return a recommended meal plan for a household/date range given constraints."""
    
    # Use household_id as provided, or default to "default_household"
    if not household_id:
        household_id = "default_household"
    
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/meals/weekly_recommendations",
    #                        {"household_id": household_id, "constraints": constraints})
    
    # Mock response for meal recommendations
    meal_plan_id = str(uuid.uuid4())
    return {
        "success": True,
        "meal_plan_id": meal_plan_id,
        "household_id": household_id,
        "constraints": constraints,
        "recommendations": [
            {
                "day": "Monday",
                "meals": [
                    {"type": "breakfast", "name": "Oatmeal with Berries", "calories": 320},
                    {"type": "lunch", "name": "Grilled Chicken Salad", "calories": 450},
                    {"type": "dinner", "name": "Salmon with Quinoa", "calories": 520}
                ]
            },
            {
                "day": "Tuesday",
                "meals": [
                    {"type": "breakfast", "name": "Greek Yogurt Parfait", "calories": 280},
                    {"type": "lunch", "name": "Turkey Wrap", "calories": 380},
                    {"type": "dinner", "name": "Vegetable Stir Fry", "calories": 420}
                ]
            },
            {
                "day": "Wednesday",
                "meals": [
                    {"type": "breakfast", "name": "Avocado Toast", "calories": 350},
                    {"type": "lunch", "name": "Quinoa Buddha Bowl", "calories": 420},
                    {"type": "dinner", "name": "Baked Cod with Sweet Potato", "calories": 480}
                ]
            },
            {
                "day": "Thursday",
                "meals": [
                    {"type": "breakfast", "name": "Smoothie Bowl", "calories": 300},
                    {"type": "lunch", "name": "Mediterranean Wrap", "calories": 400},
                    {"type": "dinner", "name": "Chicken Tikka Masala", "calories": 550}
                ]
            },
            {
                "day": "Friday",
                "meals": [
                    {"type": "breakfast", "name": "Pancakes with Maple Syrup", "calories": 380},
                    {"type": "lunch", "name": "Caesar Salad", "calories": 350},
                    {"type": "dinner", "name": "Grilled Steak with Asparagus", "calories": 520}
                ]
            },
            {
                "day": "Saturday",
                "meals": [
                    {"type": "breakfast", "name": "Eggs Benedict", "calories": 450},
                    {"type": "lunch", "name": "Fish Tacos", "calories": 420},
                    {"type": "dinner", "name": "Pasta Primavera", "calories": 480}
                ]
            },
            {
                "day": "Sunday",
                "meals": [
                    {"type": "breakfast", "name": "French Toast", "calories": 400},
                    {"type": "lunch", "name": "Grilled Cheese Sandwich", "calories": 380},
                    {"type": "dinner", "name": "Roast Chicken with Vegetables", "calories": 500}
                ]
            }
        ],
        "total_calories_per_day": 1290,
        "created_at": datetime.now().isoformat(),
        "message": "Meal recommendations generated successfully"
    }

@tool("bm_score_meal_plan", description="Call BetterMeals meal scoring API.")
async def bm_score_meal_plan(meal_id: str, metrics: list[str]) -> dict:
    """Return nutrition scores for a given meal plan."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/meals/score",
    #                        {"meal_id": meal_id, "metrics": metrics})
    
    # Mock response for meal scoring
    return {
        "success": True,
        "meal_id": meal_id,
        "metrics": metrics,
        "scores": {
            "nutrition_score": 8.5,
            "health_score": 9.2,
            "variety_score": 7.8,
            "preference_match": 8.9,
            "cost_efficiency": 7.5
        },
        "breakdown": {
            "protein": {"score": 9.0, "percentage": 25},
            "carbs": {"score": 8.0, "percentage": 45},
            "fats": {"score": 8.5, "percentage": 30},
            "fiber": {"score": 9.5, "percentage": 12},
            "vitamins": {"score": 8.8, "percentage": 95}
        },
        "recommendations": [
            "Consider adding more leafy greens for better vitamin K intake",
            "Great protein variety across meals",
            "Excellent fiber content for digestive health"
        ],
        "calculated_at": datetime.now().isoformat(),
        "message": "Meal plan scored successfully"
    }
