# Timers

State machine transitions can be triggered by the expiration of a timer. 
The corresponding transition simply declares a trigger with the name of the timer.

    t = {'source': 's0', trigger: 't0', target='s2'}


## Starting Timers

A timer can be started as part of a transition action:

    t = {'source': 'initial', trigger: 'm', target='s1', effect='start_timer("t0", "1000")'}

Similarly, a timer can be started as part of the entry or exit action of a state:

    s_0 = {'name': 's0',
            'entry': 'start_timer("t0", "1000")'}

A state must have a name, for instance `t0`. 
The duration is given in milliseconds. 
It is the minimum time until the timer's expiration, but may vary due to the state of the event queue and the load of the system.

A timer can also be started from code, using the state machine method <a href="stmpy/index.html#stmpy.Machine.start_timer">start_timer()</a> directly.
This has the advantage that the duration does not have to be hard-coded, and can depend on any calculation in code.

## Restarting a Timer

If a timer is active and `start_timer()` is called once again, the timer starts again with the new timeout.


## Stopping Timers

Timers can be stopped using the action `stop_timer()`, either using the method <a href="stmpy/index.html#stmpy.Machine.stop_timer">start_timer()</a>
or as part of a transition action:

    t = {'source': 's1', trigger: 't', target='s2', effect='stop_timer("t0")'}

As an effect, the timer will be stopped. 
If it already expired, nothing will happen.


## Checking Timer Status

In seldom cases, you may want to check in code the status of a timer. 
For that, use method <a href="stmpy/index.html#stmpy.Machine.get_timer">start_timer()</a>. 
It returns either the remaining time for that timer, or `None` if the timer is not active or does not exist.
Note that the most common patterns of accessing the status of a timer is via the state machine's states and transitions, by letting the timer expire and then change the state of a state machine, which in turn changes how other events are handled.


