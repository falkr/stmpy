# State Machines in Python

This is a simple implementation for state machines in Python. State machines define their logic in terms of states and transitions. Transitions are triggered by general event or the expirations or timers. The following features are supported:

- states and transitions
- transitions with action(s)
- initial action(s)
- timers

Support for the following concepts may be added later:

- states with entry and exit actions
- self and internal transitions
- deferred events



## Installation

    pip install stmpy

## Example: Tick Tock State Machine

    from stmpy import StateMachine
    from stmpy import Scheduler

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


    scheduler = Scheduler()
    tick = Tick()

    t1 = {'event':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick'}
    t2 = {'event':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock'}

    stm_tick = StateMachine(state='s_tick', transitions=[t1, t2], obj=tick, id='stm_tick', initial='on_init')

    tick.stm = stm_tick

    scheduler.add_stm(stm_tick)
    scheduler.start(max_transitions=5)
    scheduler.wait_until_finished()
