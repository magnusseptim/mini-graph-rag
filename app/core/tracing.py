from __future__ import annotations
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from .config import settings


def init_tracing(app) -> None:
    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)

    if settings.otlp_endpoint:
        explorer = OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
            insecure=True)

        processor = BatchSpanProcessor(explorer)
    else:
        explorer = ConsoleSpanExporter()
        processor = SimpleSpanProcessor(explorer)

    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor().instrument_app(app)
    LoggingInstrumentor().instrument(set_logging_format=True)


def get_tracer(name: str):
    return trace.get_tracer(name)
