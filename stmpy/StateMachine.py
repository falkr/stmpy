import ast

def _tid(state_id, event_id):
    return state_id + '_' + 'event_id'

class StateMachine:

    def _parse_Transitions(self, transitions):
        for transition_string in transitions:
            t_dict = transition_string #ast.literal_eval(transition_string)
            # TODO error handling: string may be written in a wrong way
            trigger = t_dict['trigger']
            source = t_dict['source']
            target = t_dict['target']
            effect = t_dict['effect']
            t_id = _tid(source, trigger)
            transition = _Transition(trigger, source, target, effect)
            # TODO error handling: what if several transition with same id start from same source state?
            self._table[t_id] = transition


    def __init__(self, first_state, transitions, obj, stm_id, initial_effects=[]):
        self._first_state = first_state
        self._state = None
        self._obj = obj
        self._initial_effects = initial_effects.split()
        self._id = stm_id
        self._table = {}
        self._parse_Transitions(transitions)


    @property
    def state(self):
        return self._state

    @property
    def id(self):
        return self._id

    @property
    def scheduler(self):
        return self._scheduler


    def _run_function(self, obj, function_name, args, kwargs):
        try:
            func = getattr(obj, function_name)
            print(str(func))
            func(*args, **kwargs)
        except AttributeError as error:
            print('Error when running function from state machine: {}'.format(error))
            #print("function {} not found on {}".format(function_name, obj))


    def _initialize(self, scheduler):
        self._scheduler = scheduler
        # run initial transition



    def _execute_transition(self, event_id, args, kwargs):
        # execute the initial transition
        if self._state is None:
            if self._initial_effects is not None:
                for function in self._initial_effects:
                    self._run_function(self._obj, function, args=[], kwargs={})
            self._state = self._first_state
        else:
            t_id = _tid(self._state, event_id)
            if t_id not in self._table:
                # TODO: error: no transition declared
                print('Error: State machine is in state {} and received event {}, but no transition with this event is declared! {} '.format(self._state, event_id, self._table))
            else:
                transition = self._table[t_id]
                for function in transition.effect:
                    self._run_function(self._obj, function, args, kwargs)

                # go into the next state
                self._state = transition.target
                print('state --> {}'.format(self._state))

    def start_timer(self, timer_id, timeout):
        self._scheduler._start_timer(timer_id, timeout, self)


    def stop_timer(self, timer_id):
        self._scheduler._stop_timer(timer_id, self)


    def send_signal(self, signal_id, args=[], kwargs={}):
        print('Add signal {}'.format(signal_id))
        self._scheduler._add_event(signal_id, args, kwargs, self)


    def terminate(self):
        self._scheduler._terminate_stm(self.id)


class _Transition:

    def __init__(self, trigger, source, target, effect):
        self.trigger = trigger
        self.source = source
        self.target = target
        self.effect = effect.split()
