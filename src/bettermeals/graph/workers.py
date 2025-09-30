from langgraph.prebuilt import create_react_agent
from ..llms.groq import worker_llm_fast
from ..tools.meals import bm_recommend_meals, bm_score_meal_plan
from ..tools.orders import bm_build_cart, bm_substitute, bm_checkout, bm_order_status
from ..tools.onboarding import bm_onboard_household, bm_onboard_resident

recommender = create_react_agent(
    model=worker_llm_fast(),
    tools=[bm_recommend_meals],
    name="meal_recommender",
    prompt="""You are a meal recommendation agent. When asked to plan meals:

1. ALWAYS call the bm_recommend_meals tool with EXACTLY these parameters:
   - household_id: string (use "default_household" if not specified)
   - constraints: object (empty {} if no dietary preferences mentioned, otherwise include preferences)

2. Present the COMPLETE meal plan in a clear format:
   - Show each day with all meals (breakfast, lunch, dinner)
   - Include meal names and calories
   - Display the meal_plan_id prominently
   - Show total calories per day

3. Format like this:
   **Meal Plan for [Household]**
   *Meal Plan ID:* **[id]**
   
   **Monday**
   - Breakfast: [name] ([calories] cal)
   - Lunch: [name] ([calories] cal)  
   - Dinner: [name] ([calories] cal)
   
   [Repeat for each day...]
   
   *Total: ~[total] calories per day*

Do not invent meals - always use the tool to get real recommendations.
"""
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
