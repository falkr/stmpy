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


__version__ = '0.6.1'
"""
The current version of stmpy.
"""

def _print_action(action):
    s = []
    s.append(action['name'])
    if action['event_args']:
        s.append('(*)')
    else:
        s.append('(')
        first = True
        for arg in action['args']:
            if first:
                s.append('{}'.format(arg))
                first = False
            else:
                s.append(', {}'.format(arg))
        s.append(')')
    return ''.join(s)

def _print_state(state):
    s = []
    s.append('{} [shape=plaintext margin=0 label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" STYLE="ROUNDED"><TR><TD><B>{}</B></TD></TR>\n'.format(state.name, state.name))
    if state.entry or state.exit:
        s.append('<HR/>')
        s.append('<TR><TD ALIGN="LEFT">')
        for entry in state.entry:
            s.append('entry / {}<BR/>'.format(_print_action(entry)))
        for exit in state.exit:
            s.append('exit / {}<BR/>'.format(_print_action(exit)))
        s.append('</TD></TR>')
    s.append('</TABLE>>];')
    return ''.join(s)

def _print_transition(t):
    s = []
    label = ''
    if t.trigger:
        label = label + t.trigger
    if t.effect:
        label = label + ' /'
        if t.trigger: label = label + '\\n'
        for effect in t.effect:
            label = label + '{};\\n'.format(_print_action(effect))
    s.append('{} -> {} [label=" {}"]\n'.format(t.source, t.target, label))
    return ''.join(s)

def get_graphviz_dot(machine):
    """
    Return the graph of the state machine.

    The format is the dot format for Graphviz, and can be directly used as input
    to Graphviz.

    To learn more about Graphviz, visit https://graphviz.gitlab.io.

    **Display in Jupyter Notebook**
    Install Python support for Graphviz via `pip install graphviz`.
    Install Graphviz.
    In a notebook, build a stmpy.Machine. Then, declare a cell with the
    following content:

        from graphviz import Source
        src = Source(stmpy.get_graphviz_dot(stm))
        src

    **Using Graphviz on the Command Line**

    Write the graph file with the following code:

        with open("graph.gv", "w") as file:
        print(stmpy.get_graphviz_dot(stm), file=file)

    You can now use the command line tools from Graphviz to create a graphic
    file with the graph. For instance:

        dot -Tsvg graph.gv -o graph.svg

    """
    s = []
    s.append('digraph G {\n')
    s.append('node [shape=box style=rounded fontname=Helvetica];\n')
    s.append('edge [ fontname=Helvetica ];\n')
    # initial state
    s.append('initial [shape=point width=0.2];\n')
    for state_name in machine._states:
        s.append(_print_state(machine._states[state_name]))
    # initial transition
    s.append(_print_transition(machine._intial_transition))
    for t_id in machine._table:
        s.append(_print_transition(machine._table[t_id]))
    s.append('}')
    return ''.join(s)

def _parse_arg_list(arglist):
    """
    Parses a list of arguments.

    Arguments are expected to be split by a comma, surrounded by any amount
    of whitespace. Arguments are then run through Python's eval() method.
    """
    args = []
    for arg in arglist.split(','):
        arg = arg.strip()
        if arg: # string is not empty
            args.append(eval(arg))
    return args

def _parse_action(action):
    """
    Parses a single action item, for instance one of the following:

        m; m(); m(True); m(*)

    The brackets must match.
    """
    i_open = action.find('(')
    if i_open is -1:
        # return action name, finished
        return {'name': action, 'args': [], 'event_args': False}
    # we need to parse the arguments
    i_close = action.rfind(')')
    if i_close is -1:
        raise Exception('Bracket in argument opened but not closed.')
    action_name = action[:i_open]
    arglist = action[i_open+1:i_close].strip()
    if not arglist:
        # no arglist, just return method name
        return {'name': action_name, 'args': [], 'event_args': False}
    if '*' in arglist:
        return {'name': action_name, 'args': [], 'event_args': True}
    return {'name': action_name, 'args': _parse_arg_list(arglist), 'event_args': False}

def _parse_action_list_attribute(attribute):
    """
    Parses a list of actions, as found in the effect attribute of
    transitions, and the enry and exit actions of states.

    Actions are separated by a semicolon, surrounded by any amount of
    whitespace. A action can have the following form:

        m; m(); m(True); m(*)

    The asterisk that the state machine should provide the args and
    kwargs from the incoming event.
    """
    actions = []
    for action_call in attribute.split(';'):
        action_call = action_call.strip()
        if action_call: # string is not empty
            actions.append(_parse_action(action_call))
    return actions

def _is_state_machine_method(name):
        return name in ['start_timer', 'stop_timer', 'send_signal']

def _current_time_millis():
    return int(round(time.time() * 1000))


def _tid(state_id, event_id):
    return state_id + '_' + event_id


class Driver:
    """
    A driver can run several  machines.

    **Run-to-completion:**
    One driver contains one thread. Machines assigned to a driver are executed
    within this single thread. This provides a strict temporal ordering of
    behavior for state machines assigned to the same driver. A driver only
    executes one transition at a time, and always executes this transition to
    completion. This means that the action within a transition can access
    shared variables without interleaving behavior. One transition is always
    executed separate from all other transitions.
    """

    _stms_by_id = {}

    def __init__(self):
        """Create a new driver."""
        self._logger = logging.getLogger(__name__)
        self._logger.debug('Logging works')
        self._active = False
        self._event_queue = Queue()
        self._timer_queue = []
        self._next_timeout = None
        # TODO need clarity if this should be a class variable
        Driver._stms_by_id = {}

    def _wake_queue(self):
        # Sends a None event to wake up the queue.
        self._event_queue.put(None)

    def print_status(self):
        """Provide a snapshot of the current status."""
        s = []
        s.append('=== State Machines: ===\n')
        for stm_id in Driver._stms_by_id:
            stm = Driver._stms_by_id[stm_id]
            s.append('    - {} in state {}\n'.format(stm.id, stm.state))
        s.append('=== Events in Queue: ===\n')
        for event in self._event_queue.queue:
            if event is not None:
                s.append('    - {} for {} with args:{} kwargs:{}\n'.format(
                    event['id'], event['stm'].id,
                    event['args'], event['kwargs']))
        s.append('=== Active Timers: {} ===\n'.format(len(self._timer_queue)))
        for timer in self._timer_queue:
            s.append('    - {} for {} with timeout {}\n'.format(
                timer['id'], timer['stm'].id, timer['timeout']))
        s.append('=== ================ ===\n')
        return ''.join(s)

    def add_machine(self, machine):
        """Add the state machine to this driver."""
        self._logger.debug('Adding machine {} to driver'.format(machine.id))
        machine._driver = self
        machine._reset()
        if machine.id is not None:
            # TODO warning when STM already registered
            Driver._stms_by_id[machine.id] = machine
            self._add_event(event_id=None, args=[], kwargs={}, stm=machine)

    def start(self, max_transitions=None, keep_active=False):
        """
        Start the driver.

        This method creates a thread which runs the event loop.
        The method returns immediately. To wait until the driver
        finishes, use `stmpy.Driver.wait_until_finished`.

        `max_transitions`: execute only this number of transitions, then stop
        `keep_active`: When true, keep the driver running even when all state
        machines terminated
        """
        self._active = True
        self._max_transitions = max_transitions
        self._keep_active = keep_active
        self.thread = Thread(target=self._start_loop)
        self.thread.start()

    def step(self, steps=1):
        """Execute a single step."""
        self.start(max_transitions=steps)
        self.wait_until_finished()

    def stop(self):
        """Stop the driver."""
        self._active = False
        self._wake_queue()

    def wait_until_finished(self):
        """Blocking method to wait until the driver finished its execution."""
        try:
            self.thread.join()
        except KeyboardInterrupt:
            self._logger.debug('Keyboard interrupt detected, stopping driver.')
            self._active = False
            self._wake_queue()

    def _sort_timer_queue(self):
        self._timer_queue = sorted(
            self._timer_queue, key=lambda timer: timer['timeout_abs'])

    def _start_timer(self, name, timeout, stm):
        self._logger.debug('Start timer with name={} from stm={}'
                           .format(name, stm.id))
        timeout_abs = _current_time_millis() + int(timeout)
        self._stop_timer(name, stm, log=False)
        self._timer_queue.append(
            {'id': name, 'timeout': timeout, 'timeout_abs': timeout_abs,
             'stm': stm, 'tid': stm.id + '_' + name})
        self._sort_timer_queue()
        self._wake_queue()

    def _stop_timer(self, name, stm, log=True):
        if log: self._logger.debug('Stopping timer with name={} from stm={}'
                                   .format(name, stm.id))
        index = 0
        index_to_delete = None
        tid = stm.id + '_' + name
        for timer in self._timer_queue:
            if timer['tid'] == tid:
                index_to_delete = index
            ++index
        if index_to_delete is not None:
            self._timer_queue.pop(index_to_delete)

    def _get_timer(self, name, stm):
        tid = stm.id + '_' + name
        for timer in self._timer_queue:
            if timer['tid'] == tid:
                return timer['timeout_abs'] - _current_time_millis()
        return None

    def _check_timers(self):
        """
        Check for expired timers.

        If there are any timers that expired, place them in the event
        queue.
        """
        if self._timer_queue:
            timer = self._timer_queue[0]
            if timer['timeout_abs'] < _current_time_millis():
                # the timer is expired, remove first element in queue
                popped = self._timer_queue.pop(0)
                # put into the event queue
                # TODO maybe put timer first in queue?
                self._logger.debug('Timer {} expired for stm {}, adding it to event queue.'.format(timer['id'], timer['stm'].id))
                self._add_event(timer['id'], [], {}, timer['stm'])
                # not necessary to set next timeout,
                # complete check timers will be called again
            else:
                self._next_timeout = (
                    timer['timeout_abs'] - _current_time_millis()) / 1000
                if self._next_timeout < 0:
                    self._next_timeout = 0
        else:
            self._next_timeout = None

    def _add_event(self, event_id, args, kwargs, stm):
        # add the event to the queue
        self._event_queue.put({'id': event_id, 'args': args, 'kwargs': kwargs,
                              'stm': stm})

    def send_signal(self, signal_id, stm_id, args=[], kwargs={}):
        """
        Send a signal to a state machine handled by this driver.

        If you have a reference to the state machine, you can also send it
        directly to it by using `stmpy.Machine.send_signal`.

        `stm_id` must be the id of a state machine earlier added to the driver.
        """
        if stm_id not in Driver._stms_by_id:
            self._logger.warn('Machine with name {} cannot be found. '
                              'Ignoring signal {}.'.format(stm_id, signal_id))
        else:
            stm = Driver._stms_by_id[stm_id]
            self._add_event(signal_id, args, kwargs, stm)

    def _terminate_stm(self, stm_id):
        self._logger.debug('Terminating machine {}.'.format(stm_id))
        # removing it from the table of machines
        Driver._stms_by_id.pop(stm_id, None)
        if not self._keep_active and not Driver._stms_by_id:
            self._logger.debug('No machines anymore, stopping driver.')
            self._active = False
            self._wake_queue()

    def _execute_transition(self, stm, event_id, args, kwargs):
        stm._execute_transition(event_id, args, kwargs)
        if self._max_transitions is not None:
            self._max_transitions = self._max_transitions-1
            if self._max_transitions == 0:
                self._logger.debug('Stopping driver because max_transitions reached.')
                self._active = False

    def _start_loop(self):
        self._logger.debug('Starting loop of the driver.')
        while self._active:
            self._check_timers()
            try:
                event = self._event_queue.get(block=True,
                                              timeout=(self._next_timeout))
                if event is not None:
                    # (None events are just used to wake up the queue.)
                    self._execute_transition(stm=event['stm'],
                                             event_id=event['id'],
                                             args=event['args'],
                                             kwargs=event['kwargs'])
            except Empty:
                # timeout has occured
                self._logger.debug('Timer expired, driver loop active again.')
            except KeyboardInterrupt:
                self.active = False
                self._logger.debug('Keyboard interrupt. Stopping the driver.')
        self._logger.debug('Driver loop is finished.')


class Machine:
    """
    Implements a state machine.

    A machine must be added to a driver to execute it.
    """

    def _parse_transitions(self, transitions):
        self._intial_transition = None
        for transition_string in transitions:
            t_dict = transition_string  # ast.literal_eval(transition_string)
            # TODO error handling: string may be written in a wrong way
            source = t_dict['source']
            if source is 'initial':
                self._intial_transition = _Transition(transition_string)
            else:
                trigger = t_dict['trigger']
                t_id = _tid(source, trigger)
                transition = _Transition(transition_string)
                # TODO error handling: what if several transition with same
                # id start from same source state?
                self._table[t_id] = transition
        if self._intial_transition is None:
            raise Exception('The machine has no initial transition')

    def _parse_states(self, states):
        for s_dict in states:
            name = s_dict['name']
            # TODO check that state name is given
            # initial state cannot be detailed
            self._states[name] = _State(s_dict)

    def __init__(self, name, transitions, obj, states=[]):
        """Create a new state machine.

        Throws an exception if the state machine is not well-formed.

        **Transitions:**
        Transitions are specified as a dictionary with the following key / value
        pairs:

          * trigger: string with the name of a trigger, either a signal to receive or the name of a timer.
          * source: string with the name of a state.
          * target: string with the name of a state.
          * effect: (optional) a set of strings that refers to method name of the object passed to the state machine via `obj`. Several effects can be separated with a `;`.

            #!python
            t_1 = {'trigger': 'tick',
                   'source': 's_tick',
                   'target': 's_tock',
                   'effect': 'on_tick'}

        **Initial Transition:**
        A state machine requires a single initial transition. This is a normal
        transition that has a source state with name `'initial'`, and no
        trigger.

            #!python
            t_0 = {'source': 'initial',
                   'target': 's_tick',
                   'effect': 'on_init'}

        **Compound Transitions:**
        A compound transition is used to declare a transition that can contain decisions.
        A compound transition can decide upon the target state at run-time, for instance based on data in variables.
        It is declared like a normal transition, but does not declare any effect or target.
        Instead, it refers to a function that is executed. The function must return a string that determines the target state.

            #!python
            def transition_1(args, kwargs):
                # do something
                if ... :
                    return 's1'
                else:
                    return 's2'

            t_3 = {'source': 's_0',
                   'trigger': 't',
                   'function': transition_1}

        **States:**
        States are specified as sources and targets as part of the transitions.
        This is done by simple strings.

        States can also declare entry and exit actions that are called when they are entered or exited.
        To declare these actions, declare a dictionary for the state. The name key refers to
        the name of the state that is also used in the transition declaration.

            #!python
            s_0 = {'name': 's_0',
                   'entry': 'op1; op2',
                   'exit': 'op3'}

        **Actions and Effects:**
        The value of the attributes for transition effects and for state entry
        and exit actions can list several actions that are called on the object
        provided to the state machine.

        This list of actions can look in the following way:

            effect='m1; m2(); m3(1, True, "a"); m4(*)'

        This is a semicolon-separated list of actions that are called, here as
        part of a transition's effect. Method m1 has no arguments, and neither
        does m2. This means the empty brackets are optional. Method m3 has three
        litteral arguments, here the integer 1, the boolean True and the string
        'a'. Note how the string is surrounded by double quotation marks, since
        the entire effect is coded in single quotation marks. Vice-versa is also
        possible. The last method, m4, declares an asterisk as argument. This
        means that the state machine uses the args and kwargs of the incoming
        event and offers them to the method.

        The actions can also directly refer to the state machine actions
        `stmpy.Machine.start_timer`, `stmpy.Machine.stop_timer`, and
        `stmpy.Machine.send_signal`. A transition can for instance declare the
        following effects:

            effect='start_timer("t1", 100); stop_timer("t2"); send_signal("a")'


        `name`: Name of the state machine. This name is used to send signals to it, and show its state during debugging.

        `transitions`: A set of transitions, as explained above. There must be at least one initial transition.

        `obj`: An object that encapsulates any actions called from states or transitions.

        `states`: Optional state declarations to add entry and exit actions to them.
        """
        self._logger = logging.getLogger(__name__)
        self._state = 'initial'
        self._obj = obj
        self._id = name
        self._table = {}
        self._states = {}
        self._parse_states(states)
        self._parse_transitions(transitions)

    @property
    def state(self):
        """Return the current control state of the machine.

        This property can be accessed for debugging only.
        """
        return self._state

    @property
    def id(self):
        """Return the name of this machine."""
        return self._id

    @property
    def driver(self):
        """Return the driver this machine is attached to."""
        return self._driver

    def _reset(self):
        self._state = 'initial'

    def _run_function(self, obj, function_name, args, kwargs):
        function_name = function_name.strip()
        self._logger.debug('Running function {}.'.format(function_name))
        try:
            func = getattr(obj, function_name)
            func(*args, **kwargs)
        except AttributeError as error:
            self._logger.error(
                'Error when running function {} from machine.'.format(
                    function_name), exc_info=True)

    def _run_state_machine_function(self, name, args, kwargs):
        if name == 'start_timer':
            if len(args) != 2:
                self._logger.error('Method {} expects 2 args.'.format(name))
            self.start_timer(args[0], args[1])
        elif name == 'stop_timer':
            if len(args) != 1:
                self._logger.error('Method {} expects 1 arg.'.format(name))
            self.stop_timer(args[0])
        else:
            self._logger.error('Action {} is not a built-in method.'.format(name))

    def _initialize(self, scheduler):
        self._driver = scheduler

    def _run_actions(self, actions, args=[], kwargs={}):
        for action in actions:
            if _is_state_machine_method(action['name']):
                self._run_state_machine_function(action['name'], action['args'], kwargs)
            elif action['event_args']:
                # use the arguments provided by the event
                self._run_function(self._obj, action['name'], args, kwargs)
            else:
                # use the static arguments provided by declaration
                self._run_function(self._obj, action['name'], action['args'], {})

    def _enter_state(self, state):
        self._logger.debug('Machine {} enters state {}'.format(self.id, state))
        # execute any entry actions
        if state in self._states:
            self._run_actions(self._states[state].entry)
        self._state = state

    def _exit_state(self, state):
        self._logger.debug('Machine {} exits state {}'.format(self.id, state))
        # execute any exit actions
        if state in self._states:
            self._run_actions(self._states[state].exit)

    def _execute_transition(self, event_id, args, kwargs):
        previous_state = self._state
        if self._state is 'initial':
            transition = self._intial_transition
        else:
            t_id = _tid(self._state, event_id)
            if t_id not in self._table:
                self._logger.warning(
                    'Machine {} is in state {} and received '
                    'event {}, but no transition with this event is declared!'
                    .format(self.id, self._state, event_id, self._table))
                return
            else:
                transition = self._table[t_id]
                self._exit_state(self._state)
        # execute all effects
        self._run_actions(transition.effect, args, kwargs)
        if transition.target:
            # simple transition
            target = transition.target
        else:
            # compound transitions defined in code
            target = transition.function(*args, **kwargs)
        # go into the next state
        self._enter_state(target)
        self._logger.debug('Transition in {} from {} to {} triggered by {}'.format(self.id, previous_state, target, event_id))

    def start_timer(self, timer_id, timeout):
        """
        Start a timer or restart an active one.

        The timeout is given in milliseconds. If a timer with the
        same name already exists, it is restarted with the specified timeout.
        Note that the timeout is intended as the minimum time until the timer's
        expiration, but may vary due to the state of the event queue and the
        load of the system.
        """
        self._logger.debug('Start timer {} in stm {}'.format(timer_id, self.id))
        self._driver._start_timer(timer_id, timeout, self)

    def stop_timer(self, timer_id):
        """
        Stop a timer.

        If the timer is not active, nothing happens.
        """
        self._logger.debug('Stop timer {} in stm {}'.format(timer_id, self.id))
        self._driver._stop_timer(timer_id, self)

    def get_timer(self, timer_id):
        """
        Gets the remaining time for the timer.

        If the timer is not active, `None` is returned.
        """
        return self._driver._get_timer(timer_id, self)

    def send_signal(self, signal_id, args=[], kwargs={}):
        """
        Send a signal to this state machine.

        To send a signal to a machine by its name, use
        `stmpy.Driver.send_signal` instead.
        """
        self._logger.debug('Send signal {} in stm {}'.format(signal_id, self.id))
        self._driver._add_event(
            event_id=signal_id, args=args, kwargs=kwargs, stm=self)

    def terminate(self):
        """
        Terminate this state machine.

        This removes it from the scheduler.
        If this is the last state machine of the scheduler and the scheduler is
        not configured to stay active, this will also terminate the scheduler.
        """
        self._driver._terminate_stm(self.id)


class _Transition:

    def __init__(self, t_dict):
        self.source = t_dict['source']
        if 'effect' in t_dict:
            self.effect = _parse_action_list_attribute(t_dict['effect'])
        else:
            self.effect = []
        if 'trigger' in t_dict:
            self.trigger = t_dict['trigger']
        else:
            self.trigger = None
        if 'function' in t_dict:
            # transition is defined by a function
            self.target = None
            self.function = t_dict['function']
        else:
            # transition is declared in data structure
            self.target = t_dict['target']


class _State:
    # TODO does not work with empty entry and exit dict entries.
    def __init__(self, s_dict):
        self.name = s_dict['name']
        if 'entry' in s_dict:
            self.entry = _parse_action_list_attribute(s_dict['entry'])
        else:
            self.entry = []
        if 'exit' in s_dict:
            self.exit = _parse_action_list_attribute(s_dict['exit'])
        else:
            self.exit = []
