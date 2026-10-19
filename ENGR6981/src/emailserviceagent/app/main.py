from fastapi import FastAPI
from app.config import settings
from app.router import router
from app.ui import ui

app = FastAPI(title=settings.APP_NAME)
app.include_router(router)
app.include_router(ui)