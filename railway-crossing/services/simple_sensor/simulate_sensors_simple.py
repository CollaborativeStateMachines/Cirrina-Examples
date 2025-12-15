import Event_pb2

import asyncio
import nats
import time
import os
import uuid

from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

START_RATE = 80000
END_RATE = 80000
INTERVALS_PER_SECOND = 6
DURATION_IN_SECONDS = 600
SLICE_DURATION = 1.0 / INTERVALS_PER_SECOND

resource = Resource(attributes={SERVICE_NAME: "railway-simulation"})
metric_exporter = OTLPMetricExporter()
metric_reader = PeriodicExportingMetricReader(metric_exporter)
provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(provider)

trace_provider = TracerProvider(resource=resource)
span_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(span_exporter)
trace_provider.add_span_processor(span_processor)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)
class Generator:
    def __init__(self, nc):
        self._nc = nc

        self._event_template = Event_pb2.Event()
        self._event_template.name = "sensor"
        self._event_template.channel = Event_pb2.Event.PERIPHERAL

        self._speed_var = self._event_template.data.add()
        self._speed_var.name = "trainSpeed"
        self._speed_var.value.double = 2500.0

        self._bool_var = self._event_template.data.add()
        self._bool_var.name = "value"

        self._trace_id_var = self._event_template.data.add()
        self._trace_id_var.name = "traceId"
        self._span_id_var = self._event_template.data.add()
        self._span_id_var.name = "spanId"

    async def run(self):
        anchor_time = time.time()
        for second_idx in range(DURATION_IN_SECONDS):
            current_interval = START_RATE + (END_RATE - START_RATE) * (second_idx / DURATION_IN_SECONDS)
            events_per_slice = int(current_interval / INTERVALS_PER_SECOND)
            for i in range(INTERVALS_PER_SECOND):
                s_value = (i % 2 == 0)
                for k in range(events_per_slice):
                    await self._publish_event(s_value, (k == 0), current_interval)
                    expected_end_time = anchor_time + second_idx + (i * SLICE_DURATION) + ((SLICE_DURATION / events_per_slice) * k)
                    sleep_time = expected_end_time - time.time()
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

    async def _publish_event(self, s_value, trace_this, current_interval):
        self._bool_var.value.bool = s_value
        self._event_template.createdTime = time.time_ns() / 1.0e6
        self._event_template.id = str(uuid.uuid4())

        if trace_this:
            with tracer.start_as_current_span("broadcast_sensor") as span:
                ctx = span.get_span_context()

                self._trace_id_var.value.string = trace.format_trace_id(ctx.trace_id)
                self._span_id_var.value.string = trace.format_span_id(ctx.span_id)
                span.set_attribute("interval", current_interval)

                await self._nc.publish("peripheral.sensor", self._event_template.SerializeToString())
        else:
            self._trace_id_var.value.string = ""
            self._span_id_var.value.string = ""

            await self._nc.publish("peripheral.sensor", self._event_template.SerializeToString())

async def main():
    nats_url = os.environ.get("NATS_URL")
    try:
        nc = await nats.connect(nats_url)
    except Exception as e:
        print(f"Error connecting to NATS: {e}")
        return

    generator = Generator(nc)
    start = time.time()
    await generator.run()
    end = time.time()

    print(f"Done. Actual Duration: {end - start:.4f} seconds")

    await nc.drain()

if __name__ == "__main__":
    asyncio.run(main())