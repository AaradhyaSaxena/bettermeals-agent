import requests
from typing import Callable, Dict, Any
from .settings import settings


EXTERNAL_ENDPOINTS: Dict[str, str] = {
    "SCORE_MEAL": f"{settings.bm_backend_api_base}/meals/score",
    "PLACE_ORDER": f"{settings.bm_backend_api_base}/orders/checkout",
}


def call_generate_meal_plan(household_id: str) -> Dict[str, Any]:
    """Call the external meal plan generation endpoint."""
    resp = requests.get(f"{settings.bm_backend_api_base}/api/v1/athena/weekly-meal-plan/{household_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def call_score_meal(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call the external meal scoring endpoint."""
    resp = requests.post(EXTERNAL_ENDPOINTS["SCORE_MEAL"], json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()

def call_place_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call the external order placement endpoint."""
    resp = requests.post(EXTERNAL_ENDPOINTS["PLACE_ORDER"], json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


EXTERNAL_METHODS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "GENERATE_MEAL_PLAN": call_generate_meal_plan,
    "SCORE_MEAL": call_score_meal,
    "PLACE_ORDER": call_place_order,
}

