# Messages

The transition of a state machine can be triggered by the reception of a message.
The corresponding transition simply declares a trigger with the name of the message.

```python
t = {'source': 's0', trigger: 'm1', target='s1'}
```

The messages can origin from the state machine itself, from another state machine, or from any other Python code.
Hence messages are useful to couple state machines with each other, or to trigger a state machine transition from code.


## Sending Messages (via the State Machine)

Messages can be sent by a state machine using the action `send()`, either using the method <a href="stmpy/index.html#stmpy.Machine.send">send()</a>
or as part of a transition action:

```python
t = {'source': 's1', trigger: 't', target='s2', effect='send("m1")'}
```

## Sending Messages (via the Driver)

To send a message to another state machine, use the <a href="stmpy/index.html#stmpy.Driver.send">send()</a> method of the driver class.
This method lets you specify the name of the receiving state machine.


## Data in Messages

In addition to their name, messages can carry data. This data can either be specified as Python args (a list of variables), or kwargs (a dictionary of variables).

When a message with args or kwargs is received, the data is offered to all actions in a transition that have an asterisk (*) as their signature.
The signature of the method must match with the passed args and kwargs.


