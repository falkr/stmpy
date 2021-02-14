# States

## Simple States

States can be declared implicitly by referring to them as sources and targets in transition declarations.
States can have meaningful names, like `idle`, `waiting` or `active`, or numeric names like `s1`.
The names `initial` and `final` are reserved for initial and final states.

## Initial States

A state machine must have exactly one initial state, declared implicitly with 
an initial transition.

```python
t0 = {'source': 'initial', 'trigger': 't', 'target'='s1'}
```

## Final States

A transition can have a state with name `final` as target. 
Once it executes, the state machine terminates and is removed from the driver. 
If this was the last machine of the driver, the driver terminates as well.

## Entry and Exit Actions

States can declare entry and exit actions that are called when they are entered or exited.
To declare these actions, declare a dictionary for the state. The name key refers to
the name of the state that is also used in the transition declaration.

```python
s_0 = {'name': 's0',
        'entry': 'op1; op2',
        'exit': 'op3'}
```

Note that you can declare several entry or exit actions, like in the example above, which has the two entry actions `op1` and `op2`, separated by a `;`.


## Do-Actions

A state can also declare a do-action. This action is started once the state is entered, 
after any entry actions, if there are any. 
Do-actions can execute code that takes a long time to run, and are executed in their own thread, 
so that they don't block the execution of other behavior. 
Once the do-action finishes, the state machine automatically dispatches an event with name `done`. 
This implies that a state with a do-action has only one outgoing transition, and this transition must be triggered by the event `done`.

```python
s1 = {'name': 's1', 
        'do': 'do_action("a")'}
```

## Deferred Events

A state can defer an event. In this case, the event, if it happens, does not trigger a transition, 
but is ignored in the input queue until the state machine switches into another state
that does not defer the event anymore. 
This is useful to handle events that can arrive in states when they are not useful yet.
To declare a deferred event, simply add the event with its name as key in the 
extended state description, and use the keyword `defer` as value:

```python
s1 = {'name': 's1', 
        'a': 'defer'}
```