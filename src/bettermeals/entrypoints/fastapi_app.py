import logging, logging.config, yaml, os
from fastapi import FastAPI
from .routes.whatsapp import router as whatsapp_router

# Basic logging config
cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "logging.yaml")
with open(cfg_path) as f:
    logging.config.dictConfig(yaml.safe_load(f))

app = FastAPI(title="BetterMeals Agents")
app.include_router(whatsapp_router, prefix="/webhooks")
