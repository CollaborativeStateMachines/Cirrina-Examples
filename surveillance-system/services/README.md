# Services

All services required by the video surveillance use case are found in [services](services) sub folder.
- `iotservices`<br>
  Camera service which simulates image capturing. Adds random noise to each image to ensure uniqueness.
- `edgeservices`<br>
  Person detection service which checks whether the provided image contains any persons.
- `cloudservices`<br>
  Service which simulates face analysis. Marks persons as threats (20% chance) or no threat (otherwise).

Used by both the Cirrina and Sonataflow version of the smart factory use case.

## Usage with Docker Compose

To run all services locally on a single device, you can use Docker Compose:

```
docker compose up
```

By default, the services will use protobuf to serialize/deserialize response/request data. This can be disabled by 
setting an environment variable beforehand:

```
PROTO=false docker compose up
```

Individual Dockerfiles for separate manual builds can be found in the respective service folders.