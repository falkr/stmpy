import ast
import logging

def _tid(state_id, event_id):
    return state_id + '_' + 'event_id'

class Machine:

    def _parse_transitions(self, transitions):
        self._intial_transition = None
        for transition_string in transitions:
            t_dict = transition_string #ast.literal_eval(transition_string)
            # TODO error handling: string may be written in a wrong way
            source = t_dict['source']
            target = t_dict['target']
            if 'effect' in t_dict:
                effect = t_dict['effect']
            else:
                effect = None
            if source is 'initial':
                self._intial_transition = _Transition(None, source, target, effect)
            else:
                trigger = t_dict['trigger']
                t_id = _tid(source, trigger)
                transition = _Transition(trigger, source, target, effect)
                # TODO error handling: what if several transition with same id start from same source state?
                self._table[t_id] = transition
        if self._intial_transition is None:
            raise Exception('The machine has no initial transition')


    def _parse_states(self, states):
        for s_dict in states:
            entry = s_dict['entry']
            exit = s_dict['exit']
            name = s_dict['name']
            # initial state cannot be detailed
            self._states[name] = _State(entry, exit)


    def __init__(self, name, transitions, obj, states=[]):
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
        return self._state

    @property
    def id(self):
        return self._id

    @property
    def scheduler(self):
        return self._driver


    def _run_function(self, obj, function_name, args, kwargs):
        function_name = function_name.strip()
        self._logger.debug('Running function {}.'.format(function_name))
        try:
            func = getattr(obj, function_name)
            func(*args, **kwargs)
        except AttributeError as error:
            self._logger.error('Error when running function {} from machine.'.format(function_name), exc_info=True)


    def _initialize(self, scheduler):
        self._driver = scheduler


    def _enter_state(self, state):
        self._logger.debug('Machine {} enter state {}'.format(id, state))
        # execute any entry actions
        if state in self._states:
            for entry in self._states[state].entry:
                self._run_function(self._obj, entry, args=[], kwargs={})
        self._state = state


    def _exit_state(self, state):
        self._logger.debug('Machine {} exits state {}'.format(id, state))
        # execute any exit actions
        if state in self._states:
            for exit in self._states[state].exit:
                self._run_function(self._obj, exit, args=[], kwargs={})


    def _execute_transition(self, event_id, args, kwargs):
        if self._state is 'initial':
            transition = self._intial_transition
        else:
            t_id = _tid(self._state, event_id)
            if t_id not in self._table:
                self._logger.error('Error: State machine is in state {} and received event {}, but no transition with this event is declared! {} '.format(self._state, event_id, self._table))
                return
            else:
                transition = self._table[t_id]
                self._exit_state(self._state)
        for function in transition.effect:
            self._run_function(self._obj, function, args, kwargs)
        # go into the next state
        self._enter_state(transition.target)


    def start_timer(self, timer_id, timeout):
        """
        Start a timer. The timeout is given in milliseconds. If a timer with the
        same name already exists, it is restarted with the specified timeout.
        Note that the timeout is intended as the minimum time until the timer's
        expiration, but may vary due to the state of the event queue and the
        load of the system.
        """
        self._driver._start_timer(timer_id, timeout, self)


    def stop_timer(self, timer_id):
        self._driver._stop_timer(timer_id, self)


    def send_signal(self, signal_id, args=[], kwargs={}):
        """
        Send a signal to this state machine.

        To send a signal to a machine by its name, use
        `stmpy.Driver.send_signal` instead.
        """
        self._driver._add_event(event_id=signal_id, args=args, kwargs=kwargs, stm=self)


    def terminate(self):
        """
        Terminate this state machine. This removes it from the scheduler.
        If this is the last state machine of the scheduler and the scheduler is
        not configured to stay active, this will also terminate the scheduler.
        """
        self._driver._terminate_stm(self.id)


class _Transition:

    def __init__(self, trigger, source, target, effect):
        self.trigger = trigger
        self.source = source
        self.target = target
        if effect:
            self.effect = effect.split(';')
        else:
            self.effect = []


class _State:

    def __init__(self, entry, exit):
        self.exit = exit.split(';')
        self.entry = entry.split(';')
