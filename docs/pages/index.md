# State Machines in Python

STMPY is a simple implementation for state machines in Python.


## Installation

STMPY is available via [Python Package Index](https://pypi.org/project/stmpy/), and you can install it via pip: 

```bash
pip install stmpy
```

To upgrade, use:

```bash
pip install --upgrade stmpy
```



## Example: Tick Tock State Machine

```python
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
t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick; start_timer("tock", 1000)'}
t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock; start_timer("tick", 1000)'}

stm_tick = Machine(transitions=[t0, t1, t2], obj=tick, name='stm_tick')
tick.stm = stm_tick

driver.add_stm(stm_tick)
driver.start(max_transitions=5)
driver.wait_until_finished()
```

## Contributing

`stmpy` [is on GitHub](https://github.com/falkr/stmpy). 
Pull requests and bug reports are welcome.






