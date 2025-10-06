import logging, logging.config, yaml, os
from fastapi import FastAPI
from .routes.whatsapp import router as whatsapp_router
from ..graph.service import graph_service

# Basic logging config
cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "logging.yaml")
with open(cfg_path) as f:
    logging.config.dictConfig(yaml.safe_load(f))

logger = logging.getLogger(__name__)

# Build the graph once at application startup
logger.info("Building LangGraph workflow...")
graph_service.build_graph()
logger.info("LangGraph workflow built successfully")

app = FastAPI(title="BetterMeals Agents")
app.include_router(whatsapp_router, prefix="/webhooks")

logger.info("FastAPI application initialised")
