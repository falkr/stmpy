import ast

def _tid(state_id, event_id):
    return state_id + '_' + 'event_id'

class StateMachine:


    def _parse_Transitions(self, transitions):
        for transition_string in transitions:
            t_dict = transition_string #ast.literal_eval(transition_string)
            # TODO error handling: string may be written in a wrong way
            event_id = t_dict['event']
            source = t_dict['source']
            target = t_dict['target']
            effect = t_dict['effect']
            t_id = _tid(source, event_id)
            transition = _Transition(event_id, source, target, effect)
            # TODO error handling: what if several transition with same id start from same source state?
            self.table[t_id] = transition


    def __init__(self, state, transitions, obj, id, initial=None):
        self.state = state
        self.obj = obj
        self.initial = initial
        self.id = id
        self.table = {}
        self._parse_Transitions(transitions)


    def _run_function(self, obj, function_name, data):
        try:
            func = getattr(obj, function_name)
            print(str(func))
            # TODO also pass the data
            func()
        except AttributeError:
            print("function {} not found".format(function_name))


    def _initialize(self, scheduler):
        self.scheduler = scheduler
        # run initial transition
        if self.initial is not None:
            self._run_function(self.obj, self.initial, None)


    def _execute_event(self, event_id, data):
        t_id = _tid(self.state, event_id)
        if t_id not in self.table:
            # TODO: error: no transition declared
            print('Error: State machine is in state {} and received event {}, but no transition with this event is declared! {} '.format(self.state, event_id, self.table))
        else:
            transition = self.table[t_id]
            self._run_function(self.obj, transition.effect, data)

            # go into the next state
            self.state = transition.target
            print('state --> {}'.format(self.state))

    def start_timer(self, timer_id, timeout):
        self.scheduler._start_timer(timer_id, timeout, self)


    def stop_timer(self, timer_id):
        self.scheduler._stop_timer(timer_id, self)


    def add_event(self, event_id, data=None):
        self.scheduler.add_event(event_id, data, self)


class _Transition:

    def __init__(self, event_id, source, target, effect):
        self.event_id = event_id
        self.source = source
        self.target = target
        self.effect = effect
