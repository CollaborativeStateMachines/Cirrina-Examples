# Cirrina examples

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE.md)

Repository containing [CSM](https://collaborativestatemachines.github.io/) examples to run using the Cirrina runtime system.

## Current Use Cases

This repository contains the following use case implementations:

- [Big](big)<br>
  Scalability benchmark testing many-to-many message routing ([More info](https://dl.acm.org/doi/abs/10.1145/2364489.2364495)).

- [Chameneos](chameneos)<br>
  Symmetrical communication benchmark involving rendezvous interactions and mutating states ([More info](https://ieeexplore.ieee.org/document/1227495)).

- [Cigarette Smokers](cigaretteSmokers)<br>
  Concurrency problem demonstrating the coordination of multiple resources via an arbitrator ([More info](https://en.wikipedia.org/wiki/Cigarette_smokers_problem)).

- [Count](count)<br>
  Benchmark evaluating the performance of message counting.

- [Dining Philosophers](diningPhilosophers)<br>
  Classic synchronization problem illustrating resource allocation and deadlock avoidance ([More info](https://en.wikipedia.org/wiki/Dining_philosophers_problem)).

- [Sleeping Barber](sleepingBarber)<br>
  Inter-process communication problem involving a finite waiting room and a shared resource ([More info](https://en.wikipedia.org/wiki/Sleeping_barber_problem)).

- [Ping Pong](pingPong)<br>
  Message-passing benchmark demonstrating synchronous communication.

Individual use case descriptions and usage instructions can be found in the corresponding README files.

## Deployment

The project provides local setups using Vagrant and Docker Compose for development. For large-scale scientific experimentation, it includes [Grid'5000](https://www.grid5000.fr/) deployment scripts that leverage [EnOSLib](https://discovery.gitlabpages.inria.fr/enoslib/) to ensure efficiency and reproducibility.