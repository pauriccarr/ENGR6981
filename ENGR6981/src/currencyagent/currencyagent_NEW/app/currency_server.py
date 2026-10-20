"""Embedded gRPC CurrencyService (hipstershop.CurrencyService) -- replaces the standalone currencyservice.

Serves GetSupportedCurrencies and Convert on GRPC_PORT using the upstream EUR-based rate table, plus the
standard grpc.health.v1 service so Kubernetes grpc probes work. The agent's own CurrencyGrpcClient points at
this server (CURRENCY_HOST=127.0.0.1), so fault injection still wraps every call.
"""
import json
import logging
import os
from concurrent import futures
from decimal import Decimal, ROUND_HALF_EVEN

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from app.clients import demo_pb2, demo_pb2_grpc
from app.config import GRPC_PORT

logger = logging.getLogger(__name__)

RATES_FILE = os.getenv(
    "CURRENCY_RATES_FILE",
    os.path.join(os.path.dirname(__file__), "data", "currency_conversion.json"),
)
NANOS = Decimal(1_000_000_000)


def load_rates(path: str = RATES_FILE) -> dict:
    with open(path) as f:
        return {code: Decimal(rate) for code, rate in json.load(f).items()}


class CurrencyService(demo_pb2_grpc.CurrencyServiceServicer):
    def __init__(self, rates: dict | None = None):
        self.rates = rates if rates is not None else load_rates()

    def GetSupportedCurrencies(self, request, context):
        return demo_pb2.GetSupportedCurrenciesResponse(currency_codes=list(self.rates))

    def Convert(self, request, context):
        frm, to_code = getattr(request, "from"), request.to_code
        if frm.currency_code not in self.rates or to_code not in self.rates:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                          f"unsupported currency: {frm.currency_code} -> {to_code}")
        amount = Decimal(frm.units) + Decimal(frm.nanos) / NANOS
        total = amount / self.rates[frm.currency_code] * self.rates[to_code]
        units = int(total)  # truncates toward zero
        nanos = int(((total - units) * NANOS).to_integral_value(ROUND_HALF_EVEN))
        if nanos >= NANOS:  # rounding carry
            units, nanos = units + 1, int(nanos - NANOS)
        return demo_pb2.Money(currency_code=to_code, units=units, nanos=nanos)


def start_grpc_server(port: int = GRPC_PORT) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_CurrencyServiceServicer_to_server(CurrencyService(), server)
    hs = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(hs, server)
    hs.set("", health_pb2.HealthCheckResponse.SERVING)
    hs.set("hipstershop.CurrencyService", health_pb2.HealthCheckResponse.SERVING)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"CurrencyService gRPC listening on :{port}")
    return server
