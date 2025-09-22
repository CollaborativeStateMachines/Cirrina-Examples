# Railway Crossing

This project provides a CSM-based implementation of a railway crossing safety system, as described in:

```
N. G. Leveson and J. L. Stolzy, "Safety Analysis Using Petri Nets," in IEEE Transactions on Software
Engineering, vol. SE-13, no. 3, pp. 386-397, March 1987, doi: 10.1109/TSE.1987.233170.
```

The implementation consists of four state machines:

- **Bell** - models the auditory warning at the crossing.
- **Light** - models the visual warning.
- **Gate** - models the physical barrier.
- **Crossing** - coordinates the bell, light, and gate based on input from nearby sensors.

The following diagram shows the interactions of all state machines:

![](diagram.svg)

The **Crossing** state machine transitions between the states **_init_**, **_away_**, **_approach_**, 
**_close_**, **_present_**, **_leaving_**, and **_left_**. The initial state **_init_** is indicated by a
double border.

The **_init_** state sets up the initial conditions of the railway crossing: the light and bell are off, and
the gate is up. Through a non-event-based (always) transition, the state machine moves to the **_away_** 
state. Sensors positioned before and after the railway crossing emit _s_ events that signal the presence (_s_)
or non-presence (_¬s_) of a train at the sensor position. By alternating presence and non-presence events, the
nearness of an approaching or departing train can be determined.

Based on an arriving train's nearness:

- **_approach_** - light and bell are turned on.
- **_close_** - gate is lowered.

The light, bell, and gate are managed in separate state machines triggered by the events: `lightOn`,
`lightOff`, `bellOn`, `bellOff`, `gateDown`, and `gateUp`.

Upon a train's departure:

- **_leaving_** - gate is raised.
- **_left_** - light and bell are turned off.

This example is describing in the 
[CSM Tutorial](https://collaborativestatemachines.github.io/learn/tutorial/).

## Structure

This use case is implemented using the CSML implementation of the Cirrina runtime system, in Pkl. Each of the
files `bell.pkl`, `crossing.pkl`, `gate.pkl`, and `light.pkl` implements the state machine logic using CSM.
The `main.pkl` provides the entry point by describing the collaborative state machine.

`services.pkl` provides the HTTP service implementation bindings.

## Running

The example can be executed using the provided Docker Compose file:

```
docker-compose up
```