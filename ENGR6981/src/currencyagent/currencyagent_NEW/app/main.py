import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.router import router as currency_router
from app.ui import ui
from app.currency_server import start_grpc_server

logger = logging.getLogger("currency-agent")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # The agent IS the currency service now: serve gRPC on GRPC_PORT alongside the HTTP API.
    server = start_grpc_server()
    try:
        yield
    finally:
        server.stop(grace=2)


app = FastAPI(title="Currency Agent", lifespan=lifespan)

app.include_router(currency_router)
app.include_router(ui)
