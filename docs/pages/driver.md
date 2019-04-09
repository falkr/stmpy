# State Machines and Drivers

State machines are implemented by a combination of the two classes *Machine* and *Driver.*

* A Machine represents a state machine diagram.
* A Driver maintains event queues and controls the execution of several machines.


# State Machines

State machines define their logic in terms of states and transitions.
Transitions are triggered by signals or the expiration or timers.

## State Machine Name

A state machine has a name that must be unique among all state machines in a driver. 
This name is used to log all events of the state machine, and as an address when sending a message to it.

## State Machine Object

If the state machine should invoke Python methods, it requires an object of a class that implements all actions.

    from stmpy import Machine, Driver

    class Tick:

      def __init__(self):
        self.ticks = 0
        self.tocks = 0

      def on_init(self):
        print('Init!')

      def on_tick(self):
        print('Tick!')
        self.ticks = self.ticks + 1

      def on_tock(self):
        print('Tock!')
        self.tocks = self.tocks + 1

    driver = Driver()
    tick = Tick()

    t0 = {'source':'initial', 'target':'s_tick', 'effect':'on_init; start_timer("tick", 1000)'}
    t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick; start_timer("tok", 1000)'}
    t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock; start_timer("tik", 1000)'}

    stm_tick = Machine(transitions=[t0, t1, t2], obj=tick, name='stm_tick')
    tick.stm = stm_tick

    driver.add_stm(stm_tick)
    driver.start()
    driver.wait_until_finished()

Above, the class `Tick` contains all methods that the state machine uses. 
Variable `tick` holds an instance of the class, and is passed to the constructor of the state machine.
Note that in many cases you need access to the state machine from the code, so therefore you can create 
variable `tick.stm` and assign the state machine to it via  `tick.stm = stm_tick`.


## Run-to-completion

One driver contains one thread. Machines assigned to a driver are executed
within this single thread. This provides a strict temporal ordering of
behavior for state machines assigned to the same driver. A driver only
executes one transition at a time, and always executes this transition to
completion. This means that the action within a transition can access
shared variables without interleaving behavior. One transition is always
executed separate from all other transitions.


# Drivers

To run a state machine, you need to add it to a driver, then start the driver:

    driver = Driver()
    tick = Tick()

    t0 = {'source':'initial', 'target':'s_tick', 'effect':'on_init; start_timer("tik", 1000)'}
    t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick; start_timer("tok", 1000)'}
    t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock; start_timer("tik", 1000)'}

    stm_tick = Machine(transitions=[t0, t1, t2], obj=tick, name='stm_tick')
    tick.stm = stm_tick

    driver.add_stm(stm_tick)
    driver.start()
    driver.wait_until_finished()


