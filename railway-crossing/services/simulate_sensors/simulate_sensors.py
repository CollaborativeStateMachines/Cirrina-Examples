import Event_pb2

import asyncio
import nats
import random

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

import uuid
import os
import time

MIN_TRAIN_SPEED_IN_MS = 25
MAX_TRAIN_SPEED_IN_MS = 38.89
TRAIN_LENGTH_IN_M = 150.0

START_INTERVAL_IN_SECONDS = float(os.environ["START_INTERVAL_IN_SECONDS"])
END_INTERVAL_IN_SECONDS = float(os.environ["END_INTERVAL_IN_SECONDS"])
DURATION_IN_SECONDS = 300

SENSOR_POSITIONS = [0.0, 200.0, 400.0]

TRAINS_INTERVAL_IN_S = 30.0

TIME_FACTOR = 1.0

resource = Resource(attributes={SERVICE_NAME: "railway-simulation"})

exporter = OTLPMetricExporter()

metric_reader = PeriodicExportingMetricReader(exporter)

provider = MeterProvider(resource=resource, metric_readers=[metric_reader])

metrics.set_meter_provider(provider)
meter = metrics.get_meter("railway")

events_published_counter = meter.create_counter("events_published")
phase_counter = meter.create_counter("phase")


class Train:
    def __init__(self, speed):
        self._position = 0.0
        self._speed_in_ms = speed
        self._length = TRAIN_LENGTH_IN_M

    def update_position(self, delta_time):
        self._position += delta_time * self._speed_in_ms

    def front_position(self):
        return self._position

    def back_position(self):
        return self._position - self._length

    def speed(self):
        return self._speed_in_ms


class Simulation:
    def __init__(self, trains_interval_in_s, sensor_positions, time_factor, nc):
        self._trains = []

        self._simulated_time_in_s = 0.0
        self._last_simulation_time_in_s = self._simulated_time_in_s

        self._trains_interval_in_s = trains_interval_in_s
        self._next_arrival_time_in_s = 0.0

        self._sensor_positions = sensor_positions
        self._sensor_values = [False for _ in self._sensor_positions]

        self._train_sensor_times = {}
        self._train_calculated_speed = {}

        self._time_factor = time_factor

        self._nc = nc

        self._start_time = time.time()

    def _new_train(self):
        train = Train(random.uniform(MIN_TRAIN_SPEED_IN_MS, MAX_TRAIN_SPEED_IN_MS))
        self._trains.append(train)
        # track enter/leave times for sensor 0
        self._train_sensor_times[train] = {"enter": None, "leave": None}

    def _update_sensor_values(self):
        # Reset all sensors each tick
        self._sensor_values = [False for _ in self._sensor_positions]
        trains_to_remove = []

        for train in self._trains:
            # Remove train once it passes the last sensor
            if train.back_position() > self._sensor_positions[-1]:
                trains_to_remove.append(train)
                continue

            # Update sensor active states
            for i, sensor_position in enumerate(self._sensor_positions):
                if train.back_position() <= sensor_position < train.front_position():
                    self._sensor_values[i] = True

            # Calculate speed when passing sensor 0
            train_times = self._train_sensor_times[train]
            sensor_pos = self._sensor_positions[0]
            if train.front_position() >= sensor_pos and train_times["enter"] is None:
                train_times["enter"] = self._simulated_time_in_s
            if (
                train.back_position() > sensor_pos
                and train_times["enter"] is not None
                and train_times["leave"] is None
            ):
                train_times["leave"] = self._simulated_time_in_s
                delta_t = train_times["leave"] - train_times["enter"]
                if delta_t > 0:
                    self._train_calculated_speed[train] = TRAIN_LENGTH_IN_M / delta_t
                else:
                    self._train_calculated_speed[train] = train.speed()

        # Clean up departed trains
        for train in trains_to_remove:
            self._trains.remove(train)
            self._train_sensor_times.pop(train, None)
            self._train_calculated_speed.pop(train, None)

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

            # Remove trains beyond the kill point and update sensors
            self._update_sensor_values()

            # Broadcast sensor values
            await self._broadcast_sensor_values()

            # Sleep to maintain broadcast rate
            await asyncio.sleep(current_interval)

    async def _broadcast_sensor_values(self):
        s = any(self._sensor_values)
        current_speed = 0.0
        for train in self._trains:
            if train in self._train_calculated_speed:
                current_speed = self._train_calculated_speed[train]
                break

        subject = "peripheral.sensor"
        print(s)
        print(current_speed)
        # Specify event data
        event = Event_pb2.Event()

        event.createdTime = time.time_ns() / 1.0e6
        event.id = str(uuid.uuid4())
        event.name = "sensor"
        event.channel = Event_pb2.Event.PERIPHERAL

        # Specify bool variable data
        variable_bool = event.data.add()
        variable_bool.name = "value"
        variable_bool.value.bool = s

        # Specify speed variable data
        variable_speed = event.data.add()
        variable_speed.name = "trainSpeed"
        variable_speed.value.double = current_speed

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
