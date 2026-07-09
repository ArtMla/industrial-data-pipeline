"""FastAPI application factory with lifespan model loading."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import db
from api.model_loader import ModelLoader
from api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    ModelLoader.load()
    yield
    await db.close_pool()


app = FastAPI(
    title="Industrial Predictive Maintenance API",
    description=(
        "Real-time machine failure prediction from sensor readings. "
        "Dataset: AI4I 2020 Predictive Maintenance (UCI ML Repository). "
        "Model: XGBoost classifier with physics-informed feature engineering."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
