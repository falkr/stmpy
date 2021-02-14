# Transitions


Transitions are declared as a dictionary referring to source and target states, 
trigger, and effect.

```python
t0 = {'source': 'initial', trigger: 't', target='s1', effect='action()'}
```

## Initial Transitions

A state machine must have exactly one initial transition. 
An initial transition is declared as normal transition, with the source referring to the keyword `initial`. An innitial transition is triggered when the state machine is started, and does hence not declare any trigger.

```python
t0 = {'source': 'initial', target='s1'}
```

## Transition Actions

The value of the attributes for transition effects can list several actions 
that are called on the object provided to the state machine.
This list of actions can look in the following way:

```python
effect='m1; m2(); m3(1, True, "a"); m4(*)'
```

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

```python
effect='start_timer("t1", 100); stop_timer("t2");'
```

## Internal Transitions

States can declare internal transitions. These are transitions that have the
same source and target state, similar to self-transitions. However, they don't ever
leave the state, so that any entry or exit actions declared in the state are not executed.
An internal transition is declared as part of the extended state definition. 
It simply lists the name of the trigger (here `a`) as key and the list of actions it executes
as value.

```python
s_0 = {'name': 's0',
        'a': 'action1(); action2()'}
```


## Decisions with Compound Transitions

Compound transitions can contain decisions, so that the target state of the
transition can depend on data computed during the execution of the transition.
To define compound transitions, declare a method that executes the transition.

```python
def transition_1(args, kwargs):
        ...
        if ... :           
            return 's1'
        else:
            return 's2'
```

The transition is defined in the following way:

```python
t_3 = {'source': 's0', trigger: 't', function: transition_1, 'targets': 's1 s2' }
```

This is similar to a simple transition, as it declares source state and trigger.
It does not declare a target state or effects, however. Instead, it refers to a
function that executes the transition, and returns the target state.
The optional key `targets` list all potential states so the state machine
graph can be generated from the information, even without parsing the function.

