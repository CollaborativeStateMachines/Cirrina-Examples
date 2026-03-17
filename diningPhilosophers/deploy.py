import logging
import time
import os
import tarfile
from pathlib import Path
import enoslib as en

en.init_logging(level=logging.INFO)

# --- Experiment parameters ---
CLUSTER           = "paradoxe"
IMAGE             = "collaborativestatemachines/cirrina:unstable"
MAIN_URI          = "https://raw.githubusercontent.com/CollaborativeStateMachines/Cirrina-Examples/refs/heads/develop/diningPhilosophers/main.pkl"
LOCAL_DEST        = "/tmp/fetched"
TIME_BEFORE_FETCH = 60 * 15
# -----------------------------

# Infrastructure reservation
conf = (
    en.G5kConf.from_settings(job_name=Path(__file__).name, walltime="0:30:00")
    .add_machine(roles=["arbitrator"], cluster=CLUSTER, nodes=1)
    .add_machine(roles=["worker"], cluster=CLUSTER, nodes=6)
)

provider = en.G5k(conf)
roles, networks = provider.init()

# Pre-deployment: prepare metrics directory with write permissions
with en.actions(roles=roles) as a:
    a.file(path="/tmp/metrics", state="absent")
    a.file(path="/tmp/metrics", state="directory", mode="0777")

# Software deployment (Docker)
registry_opts = dict(type="external", ip="docker-cache.grid5000.fr", port=80)
d = en.Docker(
    agent=roles["arbitrator"] + roles["worker"],
    bind_var_docker="/tmp/docker",
    registry_opts=registry_opts
)
d.deploy()

# Network emulation
netem = en.NetemHTB()
netem.add_constraints(
    src=roles["worker"],
    dest=roles["arbitrator"],
    delay="40ms",
    rate="1gbit",
    symmetric=True,
)
netem.deploy()

# Start containers:
# Start arbitrator
with en.actions(roles=roles["arbitrator"]) as a:
    a.docker_container(
        name="arbitrator",
        image=IMAGE,
        network_mode="host",
        volumes=["/tmp/metrics:/metrics:rw"],
        env={"RUN": "arbitrator", "MAIN_URI": MAIN_URI}
    )

# Start workers
for i, host in enumerate(roles["worker"]):
    with en.actions(pattern_hosts=host.address, roles=roles) as a:
        a.docker_container(
            name=f"w{i}",
            image=IMAGE,
            network_mode="host",
            volumes=["/tmp/metrics:/metrics:rw"],
            env={"RUN": str(i), "MAIN_URI": MAIN_URI}
        )

# Wait for data generation
print(f"--- Sleeping for {TIME_BEFORE_FETCH} seconds ---")
time.sleep(TIME_BEFORE_FETCH)

# Fetch Results
os.makedirs(LOCAL_DEST, exist_ok=True)

with en.actions(roles=roles) as a:
    # Bundle remote files
    a.archive(
        path="/tmp/metrics",
        dest="/tmp/metrics.tar.gz",
        format="gz"
    )
    # Pull to local
    a.fetch(
        src="/tmp/metrics.tar.gz",
        dest=LOCAL_DEST,
        flat=False
    )

# Flatten and extract
print("--- Cleaning up local directory structure ---")
for host in en.get_hosts(roles):
    host_dir = Path(LOCAL_DEST) / host.address
    tar_path = host_dir / "tmp" / "metrics.tar.gz"
    
    if tar_path.exists():
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=host_dir)
        
        tar_path.unlink()
        try:
            (host_dir / "tmp").rmdir()
        except OSError:
            pass # Directory not empty or already gone

print(f"--- Done. Metrics are in {LOCAL_DEST} ---")

provider.destroy()