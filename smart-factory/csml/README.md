# CSML Files

Contains the smart factory CSML files:
- CSML 1.0
  - `smart_factory_default.csml`: Default JSON version.
  - `smart_factory_develop.csml`: Default JSON version without comments.
  - `smart_factory_experiment.csml`: JSON Version used for the experiment on Grid`5000.
  - `smart_factory_no_extensions.csml`: JSON Version that does not use inheritance, abstraction, `output`, `match`, and `else`.
- CSML 2.0
  - `smart-factory.pkl`: Default Pkl version.
  - `smart-factory-job.pkl`: Default Pkl job description (ZooKeeper).

Also contains `service_implementations.json` which can be used to map service types to the `simulation-server` 
endpoints if run locally.

## Local usage with Cirrina

- Ensure `simulation-server` is running and listening to port 8000 with `--useProto=true`. Instructions can be found in
the [corresponding folder](../simulation-server).

- Launch InfluxDB, Telegraf, NATS and ZooKeeper. This can be done by running the 
[Cirrina compose.yaml](https://git.uibk.ac.at/informatik/dps/dps-dc-software/cirrina-project/cirrina/-/blob/develop/compose.yaml)
using Docker compose:

```
git clone git@git.uibk.ac.at:informatik/dps/dps-dc-software/cirrina-project/cirrina.git
cd cirrina
docker compose up
```

- Create the ZooKeeper nodes (Cirrina jobs). This can be done manually or by using the `create_jobs.py` script which
can be found in the [scripts folder](../../scripts) of this repository. Locally with a single instance, the script can
be run as follows:

```
cd scripts
pip install -r requirements.txt
python create_jobs.py \
    --csml_file "../smart-factory/csml/smart_factory_default.csml" \
    --services_file "../smart-factory/csml/service_implementations.json" \
    --local_data '{ "jobControlSystem": { "totalProducts": <PRODUCTS> }, "roboticArmSystem": { "partsPerProduct": <PARTS_PER_PRODUCT> } }'
```
`<PRODUCTS>` is the amount of products which should be produced until the application terminates. `<PARTS_PER_PRODUCT>` 
is the amount of parts which need to be assembled to produce a single product. The amount of total assemblies 
corresponds to the product of both values.

- Run Cirrina, e.g. by either
  - running the [Cirrina Docker Image](https://hub.docker.com/r/marlonetheredgeuibk/cirrina) as explained in the 
  [Cirrina repository](https://git.uibk.ac.at/informatik/dps/dps-dc-software/cirrina-project/cirrina); or by
  - building and running Cirrina manually using the 
  [Cirrina Dockerfile](https://git.uibk.ac.at/informatik/dps/dps-dc-software/cirrina-project/cirrina/-/blob/develop/Dockerfile).