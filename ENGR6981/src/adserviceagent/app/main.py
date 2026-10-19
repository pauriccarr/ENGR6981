# /srv/app/main.py
from fastapi import FastAPI
from app.router import router
from app.ui import ui
from app.config import settings

host = settings.ADSERVICE_HOST
port = settings.ADSERVICE_PORT

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)
app.include_router(ui)