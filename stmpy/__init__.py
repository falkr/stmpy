"""Module `stmpy` provides support for state machines in Python.

## Contributing

`stmpy` [is on GitHub](https://github.com/falkr/stmpy). Pull
requests and bug reports are welcome.
"""

import time
import logging
from queue import Queue
from queue import Empty
from threading import Thread

from .machine import Machine
from .driver import Driver
from .spin import to_promela
from .graphviz import to_graphviz

__all__ = ['Machine', 'Driver', 'to_promela', 'to_graphviz']

def get_graphviz_dot(machine):
    """ For compatibility. Use to_graphviz() instead. """
    return to_graphviz(machine)

__version__ = '0.7.5'
"""
The current version of stmpy.
"""

