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

      def on_tick(self):
        print('Tick!')
        self.ticks = self.ticks + 1

      def on_tock(self):
        print('Tock!')
        self.tocks = self.tocks + 1


    driver = Driver()
    tick = Tick()

    t0 = {'source':'initial', 'target':'s_tick', 'effect':'on_init; start_timer("tik", 1000)'}
    t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick; start_timer("tok", 1000)'}
    t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock; start_timer("tik", 1000)'}

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

    t_3 = {'source': 's_0', trigger: 't', function: transition_1, 'targets': 's1 s2' }

This is similar to a simple transition, as it declares source state and trigger.
It does not declare a target state or effects, however. Instead, it refers to a
function that executes the transition, and returns the target state.
The optional key `targets` list all potential states so the state machine
graph can be generated from the information, even without parsing the function.

## Internal Transitions

States can declare internal transitions. These are transitions that have the
same source and target state, similar to self-transitions. However, they don't ever
leave the state, so that any entry or exit actions declared in the state are not executed.
An internal transition is declared as part of the extended state definition. 
It simply lists the name of the trigger (here `a`) as key and the list of actions it executes
as value.

    s_0 = {'name': 's_0',
           'a': 'action1(); action2()'}

## Final States

A transition can have a state with name `final` as target, which terminates the machine.
A terminated machine is removed from the driver. If this was the last machine of the driver, 
the driver terminates as well.

**Actions and Effects:**
The value of the attributes for transition effects and for state entry
and exit actions can list several actions that are called on the object
provided to the state machine.

This list of actions can look in the following way:

    #!python
    effect='m1; m2(); m3(1, True, "a"); m4(*)'

This is a semicolon-separated list of actions that are called, here as
part of a transition's effect. Method m1 has no arguments, and neither
does m2. This means the empty brackets are optional. Method m3 has three
literal arguments, here the integer 1, the boolean True and the string
'a'. Note how the string is surrounded by double quotation marks, since
the entire effect is coded in single quotation marks. Vice-versa is also
possible. The last method, m4, declares an asterisk as argument. This
means that the state machine uses the args and kwargs of the incoming
event and offers them to the method.

The actions can also directly refer to the state machine actions
`stmpy.Machine.start_timer` and `stmpy.Machine.stop_timer`.
A transition can for instance declare the following effects:

    #!python
    effect='start_timer("t1", 100); stop_timer("t2");'

**Entry-, Exit-, and Do-Actions**

States also declare entry and exit actions that are called when they are entered or exited.
To declare these actions, declare a dictionary for the state. The name key refers to
the name of the state that is also used in the transition declaration.

    #!python
    s_0 = {'name': 's_0',
            'entry': 'op1; op2',
            'exit': 'op3'}

A state can also declare a do-action. This action is started once the state is entered, 
after any entry actions, if there are any. Do-actions can refer to code that takes a long time
to run, and are executed in their own thread, so that they don't block the execution of other 
behavior. Once the do-action finishes, the state machine automatically dispatches an event 
with name `done`. This implies that a state with a do-action has only one outgoing transition, and this
transition must be triggered by the event `done`.

    #!python
    s1 = {'name': 's1', 
          'do': 'do_action("a")'}