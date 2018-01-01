---
---

# State Machines in Python

This is a simple implementation for state machines in Python.
State machines define their logic in terms of states and transitions.
Transitions are triggered by signals or the expiration or timers.


## Current Project Status

The project is in an early stage, and some features are missing.


## Installation

    pip install engines


## Example: Tick Tock State Machine

    from engines import Machine, Driver

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
    scheduler.start(max_transitions=5)
    scheduler.wait_until_finished()
