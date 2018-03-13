---
---

# State Machines in Python

This is a simple implementation for state machines in Python.
State machines define their logic in terms of states and transitions.
Transitions are triggered by signals or the expiration or timers.


## Current Project Status

The project is in an early stage, and not all features are in place yet.


## Installation

    pip install stmpy

To upgrade, use:

    pip install --upgrade stmpy


## API Documentation

[Browse the API here.](./stmpy/index.html)


## Overview

State machines are implemented by a combination of the two classes *Machine* and *Driver.*

* A Machine represents a state machine diagram.
* A Driver maintains event queues and controls the execution of several machines.


## Example: Tick Tock State Machine

    from stmpy import Machine, Driver

    class Tick:

      def __init__(self):
        self.ticks = 0
        self.tocks = 0

      def on_init(self):
        print('Init!')
        self.stm.start_timer('tick', 1000)

      def on_tick(self):
        print('Tick!')
        self.ticks = self.ticks + 1
        self.stm.start_timer('tock', 1000)

      def on_tock(self):
        print('Tock!')
        self.tocks = self.tocks + 1
        self.stm.start_timer('tick', 1000)


    driver = Driver()
    tick = Tick()

    t0 = {'source':'initial', 'target':'s_tick', 'effect':'on_init'}
    t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick'}
    t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock'}

    stm_tick = Machine(transitions=[t0, t1, t2], obj=tick, name='stm_tick')
    tick.stm = stm_tick

    driver.add_stm(stm_tick)
    driver.start(max_transitions=5)
    driver.wait_until_finished()


## Compound Transitions

Compound transitions can contain decisions, so that the target state of the
transition can depend on data computed during the execution of the transition.
To define compound transitions, declare a method that executes the transition.


    def transition_1(args, kwargs):
         # do something
         if ... :           
             return 's1'
         else:
             return 's2'

The transition is defined in the following way:

t_3 = {'source': 's_0', trigger: 't', function: stm.transition_1}

This is similar to simple transition, as it declares source state and trigger.
It does not declare a target state or effects, however. Instead, it refers to a
function that executes the transition, and returns the target state.s
