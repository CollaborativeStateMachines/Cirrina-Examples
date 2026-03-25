import logging
import time
import os
import tarfile
from pathlib import Path
import enoslib as en
from tqdm import tqdm

en.init_logging(level=logging.INFO)

# --- Experiment parameters ---
IMAGE = "collaborativestatemachines/cirrina:unstable"
MAIN_URI = "https://raw.githubusercontent.com/CollaborativeStateMachines/Cirrina-Examples/refs/heads/develop/diningPhilosophers/main.pkl"
LOCAL_ROOT = Path("./results/diningPhilosophers/cirrina")
TIME_BEFORE_FETCH = 60 * 20
NUM_RUNS = 5
# -------------------------------------

# Infrastructure Reservation
conf = (
    en.G5kConf.from_settings(job_name=Path(__file__).name, walltime="03:00:00")
    .add_machine(roles=["arbitrator"], cluster="gros", nodes=1)
    .add_machine(roles=["worker"], cluster="gros", nodes=6)
)

provider = en.G5k(conf)
roles, networks = provider.init()
roles = en.sync_info(roles, networks)

# Initial Docker engine deployment
registry_opts = dict(type="external", ip="docker-cache.grid5000.fr", port=80)
d = en.Docker(
    agent=roles["arbitrator"] + roles["worker"],
    bind_var_docker="/tmp/docker",
    registry_opts=registry_opts,
)
d.deploy()

# Network emulation
netem = en.NetemHTB()
netem.add_constraints(
    src=roles["worker"],
    dest=roles["arbitrator"],
    delay="10ms",
    rate="1gbit",
    symmetric=True,
)
netem.deploy()

for run_idx in range(1, NUM_RUNS + 1):
    run_label = f"run{run_idx}"
    print(f"\n>>> Starting {run_label}...")

    # Ensure a fresh metrics directory on every node
    with en.actions(roles=roles) as a:
        a.file(path="/tmp/metrics", state="absent")
        a.file(path="/tmp/metrics", state="directory", mode="0777")

    # Deploy Containers
    with en.actions(roles=roles["arbitrator"]) as a:
        a.docker_container(
            name="arbitrator",
            image=IMAGE,
            network_mode="host",
            volumes=["/tmp/metrics:/metrics:rw"],
            env={"RUN": "arbitrator", "MAIN_URI": MAIN_URI},
            state="started",
        )

    for i, host in enumerate(roles["worker"]):
        with en.actions(pattern_hosts=host.address, roles=roles) as a:
            a.docker_container(
                name=f"w{i}",
                image=IMAGE,
                network_mode="host",
                volumes=["/tmp/metrics:/metrics:rw"],
                env={"RUN": str(i), "MAIN_URI": MAIN_URI},
                state="started",
            )

    # Wait for data collection
    print(f"--- {run_label}: Collecting data for {TIME_BEFORE_FETCH}s ---")
    for _ in tqdm(range(TIME_BEFORE_FETCH), desc=run_label, unit="s", mininterval=60):
        time.sleep(1)

    # Capture NTP timing data on all nodes
    with en.actions(roles=roles) as a:
        a.shell("ntpq -p > /tmp/metrics/ntp_stats.txt")

    # Fetch and Organize Results locally into run1, run2, etc.
    run_dest = LOCAL_ROOT / run_label
    run_dest.mkdir(parents=True, exist_ok=True)

    with en.actions(roles=roles) as a:
        a.archive(path="/tmp/metrics", dest="/tmp/metrics.tar.gz", format="gz")
        a.fetch(src="/tmp/metrics.tar.gz", dest=str(run_dest), flat=False)

    # Local extraction and Remote Container Cleanup
    print(f"--- {run_label}: Cleaning up and extracting ---")

    # Remove containers so they can be re-created in the next iteration
    with en.actions(roles=roles) as a:
        a.shell("docker rm -f arbitrator || true")
        for i in range(len(roles["worker"])):
            a.shell(f"docker rm -f w{i} || true")

    # Local file flattening
    for host in en.get_hosts(roles):
        host_dir = run_dest / host.address
        tar_path = host_dir / "tmp" / "metrics.tar.gz"

        if tar_path.exists():
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=host_dir)

            tar_path.unlink()
            try:
                (host_dir / "tmp").rmdir()
            except OSError:
                pass

print(f"\n--- SUCCESS: All {NUM_RUNS} runs finished. Data in {LOCAL_ROOT} ---")
provider.destroy()
