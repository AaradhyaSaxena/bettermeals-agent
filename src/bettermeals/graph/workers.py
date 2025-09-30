from langgraph.prebuilt import create_react_agent
from ..llms.groq import worker_llm_fast
from ..tools.meals import bm_recommend_meals, bm_score_meal_plan
from ..tools.orders import bm_build_cart, bm_substitute, bm_checkout, bm_order_status
from ..tools.onboarding import bm_onboard_household, bm_onboard_resident

recommender = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_recommend_meals],
    name="meal_recommender",
    prompt="Use the tool to get recommendations. Do not invent meals."
)

scorer = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_score_meal_plan],
    name="meal_scorer",
    prompt="Use the tool to get scores. Do not invent scores."
)

order_agent = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_build_cart, bm_substitute, bm_checkout, bm_order_status],
    name="order",
    prompt="Build cart, handle substitutions with user approval, then checkout using an idempotency key."
)

onboarding = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_onboard_household, bm_onboard_resident],
    name="onboarding",
    prompt="Convert free text to structured payloads and call the onboarding tools. Do not fabricate IDs."
)

cook_update = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_substitute],
    name="cook_update",
    prompt="Map cook messages (missing items) to substitution tool calls. Keep replies concise."
)
