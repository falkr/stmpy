import logging
from threading import Thread
from ast import literal_eval


def _parse_arg_list(arglist):
    """
    Parses a list of arguments.

    Arguments are expected to be split by a comma, surrounded by any amount
    of whitespace. Arguments are then run through Python's eval() method.
    """
    args = []
    for arg in arglist.split(","):
        arg = arg.strip()
        if arg:  # string is not empty
            args.append(literal_eval(arg))
    return args


def _parse_action(action):
    """
    Parses a single action item, for instance one of the following:

        m; m(); m(True); m(*)

    The brackets must match.
    """
    i_open = action.find("(")
    if i_open == -1:
        # return action name, finished
        return {"name": action, "args": [], "event_args": False}
    # we need to parse the arguments
    i_close = action.rfind(")")
    if i_close == -1:
        raise Exception("Bracket in argument opened but not closed.")
    action_name = action[:i_open]
    arglist = action[i_open + 1 : i_close].strip()
    if not arglist:
        # no arglist, just return method name
        return {"name": action_name, "args": [], "event_args": False}
    if "*" in arglist:
        return {"name": action_name, "args": [], "event_args": True}
    return {"name": action_name, "args": _parse_arg_list(arglist), "event_args": False}


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
    for action_call in attribute.split(";"):
        action_call = action_call.strip()
        if action_call:  # string is not empty
            actions.append(_parse_action(action_call))
    return actions


def _is_state_machine_method(name):
    return name in ["start_timer", "stop_timer", "send", "terminate"]


def _tid(state_id, event_id):
    return state_id + "_" + event_id


class Machine:
    """
    Implements a state machine.

    A machine must be added to a driver to execute it.
    """

    def _parse_transitions(self, transitions, states):
        self._initial_transition = None
        for transition_string in transitions:
            t_dict = transition_string  # ast.literal_eval(transition_string)
            # TODO error handling: string may be written in a wrong way
            source = t_dict["source"]
            if source == "initial":
                self._initial_transition = _Transition(transition_string)
            else:
                trigger = t_dict["trigger"]
                t_id = _tid(source, trigger)
                transition = _Transition(transition_string)
                # TODO error handling: what if several transition with same
                # id start from same source state?
                self._table[t_id] = transition
        if self._initial_transition is None:
            raise Exception("The machine has no initial transition")
        # parse states for internal transitions
        for s_dict in states:
            source = s_dict["name"]
            for key in s_dict.keys():
                if key not in ["name", "entry", "exit"]:
                    t_id = _tid(source, key)
                    transition = _Transition(
                        {
                            "source": source,
                            "target": source,
                            "effect": s_dict[key],
                            "internal": True,
                        }
                    )
                    self._table[t_id] = transition

    def _parse_states(self, states):
        for s_dict in states:
            name = s_dict["name"]
            # TODO check that state name is given
            # initial state cannot be detailed
            self._states[name] = _State(s_dict)

    def __init__(self, name, transitions, obj, states=None):
        """Create a new state machine.

        Throws an exception if the state machine is not well-formed.

        **Transitions:**
        Transitions are specified as a dictionary with the following key / value
        pairs:

          * trigger: string with the name of a trigger, either a message to receive or the name of a timer.
          * source: string with the name of a state.
          * target: string with the name of a state.
          * effect: (optional) a set of strings that refers to method name of the object passed to the state machine via `obj`. Several effects can be separated with a `;`.

            #!python
            t_1 = {'trigger': 'tick',
                   'source': 's_tick',
                   'target': 's_tock',
                   'effect': 'on_tick'}

        **Initial Transition:**
        A state machine must have a single initial transition. This is a normal
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
        The key 'targets' (notice the plural 's') allows to specify the potential target states.
        This has no influence on the behavior of the state machine, but is just used when the data structure is also
        used to generate a state machine graph.

            #!python
            def transition_1(args, kwargs):
                # do something
                if ... :
                    return 's1'
                else:
                    return 's2'

            t_3 = {'source': 's_0',
                   'trigger': 't',
                   'targets': 's1 s2',
                   'function': transition_1}

        **States:**
        States are specified as sources and targets as part of the transitions.
        This is done by simple strings. The name `initial` refers to the initial state
        of the state machine. (An initial transition is necessary, see above.)
        The name `final` refers to the final state of the machine.
        Once a machine executes a transition with target state `final`, it terminates.

        States can declare internal transitions. These are transitions that have the
        same source and target state, similar to self-transitions. However, they don't ever
        leave the state, so that any entry or exit actions declared in the state are not executed.
        An internal transition is declared as part of the extended state definition.
        It simply lists the name of the trigger (here `a`) as key and the list of actions it executes
        as value.

            #!python
            s_0 = {'name': 's_0',
            'a': 'action1(); action2()'}

        **Deferred Events**

        A state can defer an event. In this case, the event, if it happens, does not trigger a transition,
        but is ignored in the input queue until the state machine switches into another state
        that does not defer the event anymore.
        This is useful to handle events that can arrive in states when they are not useful yet.
        To declare a deferred event, simply add the event with its name as key in the
        extended state description, and use the keyword `defer` as value:

            #!python
            s1 = {'name': 's1',
                'a': 'defer'}

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

        `name`: Name of the state machine. This name is used to send messages to it, and show its state during debugging.

        `transitions`: A set of transitions, as explained above. There must be at least one initial transition.

        `obj`: An object that encapsulates any actions called from states or transitions.

        `states`: Optional state declarations to add entry and exit actions to them.
        """
        self._logger = logging.getLogger(__name__)
        self._state = "initial"
        self._obj = obj
        self._id = name
        self._table = {}
        self._states = {}
        if states == None:
            states = []
        self._parse_states(states)
        self._parse_transitions(transitions, states)
        self._defer_queue = None

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
        self._state = "initial"

    def _run_function(self, obj, function_name, args, kwargs, asynchronous=False):
        function_name = function_name.strip()
        self._logger.debug("Running function {}.".format(function_name))
        func = getattr(obj, function_name)
        if asynchronous:

            def running(function, args, kwargs):
                try:
                    function(*args, **kwargs)
                except AttributeError as error:
                    self._logger.error(
                        "Error when running function {} from machine.".format(
                            function_name
                        ),
                        exc_info=True,
                    )
                # dispatch completion event
                self._logger.debug(
                    "Do action complete, sending completion action after done.".format()
                )
                self._driver._add_event(
                    event_id="done", args=args, kwargs=kwargs, stm=self
                )

            function = getattr(obj, function_name.strip())
            thread = Thread(target=running, args=[function, args, kwargs])
            thread.start()
            self._logger.debug("Started do action.".format())
        else:
            try:
                func(*args, **kwargs)
            except AttributeError as error:
                self._logger.error(
                    "Error when running function {} from machine.".format(
                        function_name
                    ),
                    exc_info=True,
                )

    def _run_state_machine_function(self, name, args, kwargs):
        if name == "start_timer":
            if len(args) != 2:
                self._logger.error("Method {} expects 2 args.".format(name))
            self.start_timer(args[0], args[1])
        elif name == "stop_timer":
            if len(args) != 1:
                self._logger.error("Method {} expects 1 arg.".format(name))
            self.stop_timer(args[0])
        elif name == "terminate":
            self.terminate()
        else:
            self._logger.error("Action {} is not a built-in method.".format(name))

    def _initialize(self, driver):
        self._driver = driver

    def _run_actions(self, actions, args=None, kwargs=None):
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}
        for action in actions:
            if action["event_args"]:  # use the arguments provided by the event
                args, kwargs = args, kwargs
            else:  # use the arguments provided in the declaration
                args, kwargs = action["args"], {}
            if _is_state_machine_method(action["name"]):
                self._run_state_machine_function(action["name"], args, kwargs)
            else:
                self._run_function(self._obj, action["name"], args, kwargs)

    def _defers_event(self, event_id):
        if self._state in self._states:
            return event_id in self._states[self._state].defer
        return False

    def _add_to_defer_queue(self, event):
        if self._defer_queue is None:
            self._defer_queue = []
        # add at beginning, because we reverse when putting back
        self._defer_queue.insert(0, event)

    def _enter_state(self, state, args, kwargs):
        self._logger.debug("Machine {} enters state {}".format(self.id, state))
        if (
            self._state != state
            and self._defer_queue != None
            and len(self._defer_queue) > 0
        ):
            self._logger.debug(
                "Machine {} transfers back {} deferred events into event queue.".format(
                    self.id, len(self._defer_queue)
                )
            )
            self._driver._event_queue.queue.extendleft(self._defer_queue)
            self._defer_queue.clear()
        self._state = state
        if state in self._states:
            # execute any entry actions
            self._run_actions(self._states[state].entry)
            # execute any do actions
            if self._states[state].do:
                do_action = self._states[state].do[0]
                if do_action["event_args"]:
                    self._run_function(
                        self._obj, do_action["name"], args, kwargs, asynchronous=True
                    )
                else:
                    self._run_function(
                        self._obj,
                        do_action["name"],
                        do_action["args"],
                        {},
                        asynchronous=True,
                    )

    def _exit_state(self, state):
        self._logger.debug("Machine {} exits state {}".format(self.id, state))
        # execute any exit actions
        if state in self._states:
            self._run_actions(self._states[state].exit)

    def _execute_transition(self, event_id, args, kwargs):
        previous_state = self._state
        if self._state == "initial":
            transition = self._initial_transition
        else:
            t_id = _tid(self._state, event_id)
            if t_id not in self._table:
                self._logger.warning(
                    "Machine {} is in state {} and received "
                    "event {}, but no transition with this event is declared!".format(
                        self.id, self._state, event_id
                    )
                )
                return
            else:
                transition = self._table[t_id]
                if not transition.internal:
                    self._exit_state(self._state)
        # execute all effects
        self._run_actions(transition.effect, args, kwargs)
        if transition.internal:
            self._logger.debug(
                "Internal transition in {} state {} triggered by {}".format(
                    self.id, previous_state, event_id
                )
            )
        else:
            if transition.target:
                # simple transition
                target = transition.target
            else:
                # compound transitions defined in code
                target = transition.function(*args, **kwargs)
            # go into the next state
            if target == "final":
                self.terminate()
                self._logger.debug(
                    "Transition in {} from {} to final state triggered by {}".format(
                        self.id, previous_state, event_id
                    )
                )
            else:
                self._enter_state(target, args, kwargs)
                self._logger.debug(
                    "Transition in {} from {} to {} triggered by {}".format(
                        self.id, previous_state, target, event_id
                    )
                )

    def start_timer(self, timer_id, timeout):
        """
        Start a timer or restart an active one.

        The timeout is given in milliseconds. If a timer with the
        same name already exists, it is restarted with the specified timeout.
        Note that the timeout is intended as the minimum time until the timer's
        expiration, but may vary due to the state of the event queue and the
        load of the system.
        """
        self._logger.debug("Start timer {} in stm {}".format(timer_id, self.id))
        self._driver._start_timer(timer_id, timeout, self)

    def stop_timer(self, timer_id):
        """
        Stop a timer.

        If the timer is not active, nothing happens.
        """
        self._logger.debug("Stop timer {} in stm {}".format(timer_id, self.id))
        self._driver._stop_timer(timer_id, self)

    def get_timer(self, timer_id):
        """
        Gets the remaining time for the timer.

        If the timer is not active, `None` is returned.
        """
        return self._driver._get_timer(timer_id, self)

    def send(self, message_id, args=None, kwargs=None):
        """
        Send a message to this state machine.

        To send a message to a state machine by its name, use
        `stmpy.Driver.send` instead.
        """
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}
        self._logger.debug("Send {} in stm {}".format(message_id, self.id))
        self._driver._add_event(event_id=message_id, args=args, kwargs=kwargs, stm=self)

    def terminate(self):
        """
        Terminate this state machine.

        This removes it from the driver.
        If this is the last state machine of the driver and the driver is
        not configured to stay active, this will also terminate the driver.
        """
        self._driver._terminate_stm(self.id)


class _Transition:
    def __init__(self, t_dict):
        self.source = t_dict["source"]
        if "effect" in t_dict:
            self.effect = _parse_action_list_attribute(t_dict["effect"])
        else:
            self.effect = []
        if "trigger" in t_dict:
            self.trigger = t_dict["trigger"]
        else:
            self.trigger = None
        if "function" in t_dict:
            # transition is defined by a function
            self.target = None
            self.function = t_dict["function"]
            if "targets" in t_dict:
                self.targets = t_dict["targets"].strip().split(" ")
        else:
            # transition is declared in data structure
            self.target = t_dict["target"]
        if "internal" in t_dict:
            self.internal = t_dict["internal"]
        else:
            self.internal = False


class _State:
    # TODO does not work with empty entry and exit dict entries.
    def __init__(self, s_dict):
        self.name = s_dict["name"]
        if "entry" in s_dict:
            self.entry = _parse_action_list_attribute(s_dict["entry"])
        else:
            self.entry = []
        if "exit" in s_dict:
            self.exit = _parse_action_list_attribute(s_dict["exit"])
        else:
            self.exit = []
        if "do" in s_dict:
            self.do = _parse_action_list_attribute(s_dict["do"])
        else:
            self.do = []
        self.internal = []
        self.defer = []
        for key in s_dict.keys():
            if key not in ["entry", "exit", "name", "do"]:
                value = s_dict[key]
                if value.strip().lower() == "defer":
                    self.defer.append(key)
                else:
                    self.internal.append({"trigger": key, "effect_string": s_dict[key]})
