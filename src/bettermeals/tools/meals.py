from langchain_core.tools import tool
from ..config.settings import settings
from .http_client import post_json
import uuid
from datetime import datetime, timedelta

@tool("bm_recommend_meals", description="Call BetterMeals recommendations API.")
async def bm_recommend_meals(household_id: str, date_range: dict, constraints: dict) -> dict:
    """Return a recommended meal plan for a household/date range given constraints."""
    # TODO: Uncomment when API is working
    # return await post_json(f"{settings.bm_api_base}/meals/weekly_recommendations",
    #                        {"household_id": household_id, "date_range": date_range, "constraints": constraints})
    
    # Mock response for meal recommendations
    meal_plan_id = str(uuid.uuid4())
    return {
        "success": True,
        "meal_plan_id": meal_plan_id,
        "household_id": household_id,
        "date_range": date_range,
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
