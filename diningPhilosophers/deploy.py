import logging
from pathlib import Path
import enoslib as en

en.init_logging(level=logging.INFO)

CLUSTER = "paradoxe"
MAIN_URI = "https://raw.githubusercontent.com/CollaborativeStateMachines/Cirrina-Examples/refs/heads/develop/diningPhilosophers/main.pkl"
IMAGE = "collaborativestatemachines/cirrina:unstable"

conf = (
    en.G5kConf.from_settings(job_name=Path(__file__).name, walltime="0:30:00")
    .add_machine(roles=["arbitrator"], cluster=CLUSTER, nodes=1)
    .add_machine(roles=["worker"], cluster=CLUSTER, nodes=6)
)

provider = en.G5k(conf)
roles, networks = provider.init()

registry_opts = dict(type="external", ip="docker-cache.grid5000.fr", port=80)
d = en.Docker(
    agent=roles["arbitrator"] + roles["worker"],
    bind_var_docker="/tmp/docker",
    registry_opts=registry_opts
)
d.deploy()

with en.actions(roles=roles["arbitrator"]) as a:
    a.docker_container(
        name="arbitrator",
        image=IMAGE,
        network_mode="host",
        env={"RUN": "arbitrator", "MAIN_URI": MAIN_URI}
    )

for i, host in enumerate(roles["worker"]):
    with en.actions(pattern_hosts=host.address, roles=roles) as a:
        a.docker_container(
            name=f"w{i}",
            image=IMAGE,
            network_mode="host",
            env={
                "RUN": str(i),
                "MAIN_URI": MAIN_URI
            }
        )