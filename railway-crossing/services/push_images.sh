#!/usr/bin/bash

set +e

docker build --pull -t "marlonetheredgeuibk/cirrina-examples-railway-services:develop" -f services/Dockerfile services
docker build --pull -t "marlonetheredgeuibk/cirrina-examples-railway-simulate-sensors:develop" -f simulate_sensors/Dockerfile simulate_sensors

docker push "index.docker.io/marlonetheredgeuibk/cirrina-examples-railway-services:develop"
docker push "index.docker.io/marlonetheredgeuibk/cirrina-examples-railway-simulate-sensors:develop"