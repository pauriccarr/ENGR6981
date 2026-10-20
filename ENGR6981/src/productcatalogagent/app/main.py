from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.router import router
from app.ui import ui
from app.grpc_server import start_grpc_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    # gRPC on GRPC_PORT (3550) for the frontend, HTTP on 8080 for the agent API
    server = start_grpc_server()
    yield
    server.stop(grace=5)


app = FastAPI(title="Product Catalog Agent", lifespan=lifespan)
app.include_router(router)
app.include_router(ui)