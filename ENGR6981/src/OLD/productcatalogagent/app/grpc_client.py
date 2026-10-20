import logging
import os
from concurrent import futures

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.agent import ProductCatalogAgent
from app.clients import demo_pb2
from app.clients import demo_pb2_grpc

log = logging.getLogger(__name__)

GRPC_PORT = os.getenv("GRPC_PORT", "3550")

agent = ProductCatalogAgent()


def _dict_to_product(p: dict) -> demo_pb2.Product:
    price = p.get("price_usd") or {}
    return demo_pb2.Product(
        id=p.get("id", ""),
        name=p.get("name", ""),
        description=p.get("description", ""),
        picture=p.get("picture", ""),
        categories=list(p.get("categories", [])),
        price_usd=demo_pb2.Money(
            currency_code=price.get("currency_code", ""),
            units=int(price.get("units", 0)),
            nanos=int(price.get("nanos", 0)),
        ),
    )


class ProductCatalogAgentServicer(demo_pb2_grpc.ProductCatalogServiceServicer):
    """Serves the original hipstershop.ProductCatalogService API so the
    frontend (and other callers) can use the agent as a drop-in replacement."""

    def ListProducts(self, request, context):
        result = agent.run(query="list all products")
        return demo_pb2.ListProductsResponse(
            products=[_dict_to_product(p) for p in result["data"]])

    def GetProduct(self, request, context):
        result = agent.run(query=f"get product {request.id}", product_ids=[request.id])
        if not result["data"]:
            context.abort(grpc.StatusCode.NOT_FOUND, f"no product with ID {request.id}")
        return _dict_to_product(result["data"][0])

    def SearchProducts(self, request, context):
        result = agent.run(query=request.query)
        return demo_pb2.SearchProductsResponse(
            results=[_dict_to_product(p) for p in result["data"]])


def start_grpc_server() -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_ProductCatalogServiceServicer_to_server(
        ProductCatalogAgentServicer(), server)

    health_servicer = health.HealthServicer()
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    log.info(f"gRPC ProductCatalogService listening on :{GRPC_PORT}")
    return server
