import Event_pb2

import asyncio
import nats

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

import uuid
import os
import time

TRAIN_SPEED_IN_MS = 33.3
TRAIN_LENGTH_IN_M = 150.0

START_INTERVAL_IN_SECONDS = float(os.environ["START_INTERVAL_IN_SECONDS"])
END_INTERVAL_IN_SECONDS = float(os.environ["END_INTERVAL_IN_SECONDS"])
DURATION_IN_SECONDS = 300

SENSOR_POSITIONS = [0.0, 200.0, 400.0]

TRAINS_INTERVAL_IN_S = 30.0

TIME_FACTOR = 1.0

resource = Resource(attributes={SERVICE_NAME: "railway-simulation"})

exporter = OTLPMetricExporter(endpoint=os.environ["OTLP_ENDPOINT"])

metric_reader = PeriodicExportingMetricReader(
    exporter, export_interval_millis=int(os.environ["METRICS_INTERVAL"])
)

provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

metrics.set_meter_provider(provider)
meter = metrics.get_meter("railway")

events_published_counter = meter.create_counter("events_published")
phase_counter = meter.create_counter("phase")


class Train:
    def __init__(self):
        self._position = 0.0
        self._speed_in_ms = TRAIN_SPEED_IN_MS
        self._length = TRAIN_LENGTH_IN_M

    def update_position(self, delta_time):
        self._position += delta_time * self._speed_in_ms

    def front_position(self):
        return self._position

    def back_position(self):
        return self._position - self._length


class Simulation:
    def __init__(self, trains_interval_in_s, sensor_positions, time_factor, nc):
        self._trains = []

        self._simulated_time_in_s = 0.0
        self._last_simulation_time_in_s = self._simulated_time_in_s

        self._trains_interval_in_s = trains_interval_in_s
        self._next_arrival_time_in_s = 0.0

        self._sensor_positions = sensor_positions
        self._sensor_values = [False for _ in self._sensor_positions]

        self._time_factor = time_factor

        self._nc = nc

        self._start_time = time.time()

    def _new_train(self):
        train = Train()
        self._trains.append(train)

    def _update_sensor_values(self):
        for i, sensor_position in enumerate(self._sensor_positions):
            self._sensor_values[i] = any(
                train.back_position() <= sensor_position < train.front_position()
                for train in self._trains
            )

    def _compute_broadcast_interval(self):
        elapsed_time = time.time() - self._start_time
        if elapsed_time > DURATION_IN_SECONDS:
            # Reset the start time and elapsed time to loop
            self._start_time = time.time()
            elapsed_time = 0

            phase_counter.add(1)

        # Linear interpolation
        return START_INTERVAL_IN_SECONDS + (
            END_INTERVAL_IN_SECONDS - START_INTERVAL_IN_SECONDS
        ) * (elapsed_time / DURATION_IN_SECONDS)

    async def simulate(self):
        while True:
            # Compute current broadcast interval
            current_interval = self._compute_broadcast_interval()

            current_simulation_time = self._simulated_time_in_s
            delta_simulation_time = current_interval * self._time_factor

            self._last_simulation_time_in_s = current_simulation_time
            self._simulated_time_in_s += delta_simulation_time

            # Spawn new trains
            if self._simulated_time_in_s >= self._next_arrival_time_in_s:
                self._new_train()
                self._next_arrival_time_in_s += self._trains_interval_in_s

            # Update train positions
            for train in self._trains:
                train.update_position(delta_simulation_time)

            # Remove trains beyond the kill point
            self._trains = [
                train
                for train in self._trains
                if train.back_position() < self._sensor_positions[-1]
            ]

            # Update sensor values
            self._update_sensor_values()

            # Broadcast sensor values
            await self._broadcast_sensor_values()

            # Sleep to maintain broadcast rate
            await asyncio.sleep(current_interval)

    async def _broadcast_sensor_values(self):
        s = False

        for i, sensor_value in enumerate(self._sensor_values):
            s = s or sensor_value

        subject = "peripheral.sensor"

        # Specify event data
        event = Event_pb2.Event()

        event.createdTime = time.time_ns() / 1.0e6
        event.id = str(uuid.uuid4())
        event.name = "sensor"
        event.channel = Event_pb2.Event.PERIPHERAL

        # Specify variable data
        variable = event.data.add()

        variable.name = "value"
        variable.value.bool = s

        # Publish event
        await self._nc.publish(subject, event.SerializeToString())

        events_published_counter.add(1)


async def main():
    nats_url = os.environ["NATS_URL"]

    nc = await nats.connect(nats_url)

    print(f"Running sensor simulation, NATS URL={nats_url}")

    simulation = Simulation(TRAINS_INTERVAL_IN_S, SENSOR_POSITIONS, TIME_FACTOR, nc)
    await simulation.simulate()

    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
