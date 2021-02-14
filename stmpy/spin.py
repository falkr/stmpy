import textwrap


class Promela:
    def __init__(self, machines):
        self.machines = machines
        # all triggers used in all machines
        self.machine_to_triggers = {}
        self.machine_to_timers = {}
        self.machine_to_defers = {}
        self.machines_that_defer = []
        self.machines_with_final_state = []
        self.uses_timers = False
        self.uses_defer = False
        for machine in self.machines:
            triggers = []
            timers = []
            for transition in machine._table.values():
                if transition.trigger is not None:
                    triggers.append(transition.trigger)
                    # TODO: convention that timers start with 't'
                    if transition.trigger.startswith("t"):
                        self.uses_timers = True
                        timers.append(transition.trigger)
                if transition.target == "final":
                    self.machines_with_final_state.append(machine)
            self.machine_to_triggers[machine._id] = set(triggers)
            self.machine_to_timers[machine._id] = set(timers)
            defers = []
            for state in machine._states.values():
                if len(state.defer) > 0:
                    defers.extend(state.defer)
                    self.machines_that_defer.append(machine)
                    self.uses_defer = True
            self.machine_to_defers[machine._id] = set(defers)
        self.all_triggers = []
        for triggers in self.machine_to_triggers.values():
            self.all_triggers.extend(triggers)
        self.all_triggers = set(self.all_triggers)
        self.machines_that_defer = set(self.machines_that_defer)
        self.machines_with_final_state = set(self.machines_with_final_state)

    def to_promela(self):
        s = []
        mtypes = self.all_triggers.copy()
        mtypes.add("stop")
        s.append("mtype {{{}}};".format(", ".join(mtypes)))

        timer_process = textwrap.dedent(
            """\
            proctype Timer (chan queue, tc; mtype name) {
              if
              /* the timer expires */
              :: skip -> queue ! name;
              /* the timer is stopped */
              :: tc ? stop -> skip;
              fi;
            }"""
        )

        inline_defer = textwrap.dedent(
            """\
            inline save(msg) {
              atomic {
                queue ? msg ->
                printf("SAVE %e\n", msg);
                queue_temp ! msg;
              }
            }"""
        )
        # queue ? msg -> printf(\"DISCARD %e\n\", msg);
        inline_discard = textwrap.dedent(
            """\
            inline discard(msg) {
              atomic {
                queue ? msg -> skip;
              }
            }"""
        )
        inline_requeue = textwrap.dedent(
            """\
            inline requeue() {
              atomic {
                do
                :: queue ? msg -> queue_temp ! msg;
                :: empty(queue) -> break;
                od;
                do
                :: queue_temp ? msg -> queue ! msg;
                :: empty(queue_temp) -> break;
                od;
              }
            }"""
        )
        if self.uses_timers:
            s.append("")
            s.append(timer_process)
        if self.uses_defer:
            s.append("")
            s.append(inline_defer)
            s.append("")
            s.append(inline_requeue)
        s.append(inline_discard)
        s.append("")
        for machine in self.machines:
            self.to_p_stm(machine, s)
        s.append("")
        s.append("init {")
        for machine in self.machines:
            s.append("  chan to_{} = [10] of {{mtype}};".format(machine._id))
            s.append("  run {}(to_{});".format(machine._id, machine._id))
        s.append("}")
        return "\n".join(s)

    def to_p_stm(self, machine, s):
        requeue = machine in self.machines_that_defer
        s.append("proctype {} (chan queue) {{".format(machine._id))
        s.append("\n")
        if requeue:
            s.append("  chan queue_temp = [16] of {mtype};")
        for timer in self.machine_to_timers[machine._id]:
            s.append("  chan {}_c = [1] of {{mtype}};".format(timer))
        s.append("  mtype msg;")
        s.append("\n")
        # initial transition
        s.append("  initial:")
        s.append("    atomic {")
        self._effect(machine._initial_transition, s)
        self._next_state(machine._initial_transition, s)
        s.append("    }")
        s.append("\n")

        # complex states, defined as dicts
        complex_states = []
        for state in machine._states:
            complex_states.append(state.name)
            _state(self, state, machine, s, requeue)
            s.append("")
        # simple states, only defined by transitions
        simple_states = []
        for transition in machine._table.values():
            if transition.source not in complex_states:
                simple_states.append(transition.source)
        simple_states = set(simple_states)
        for state in simple_states:
            self._state_simple(state, machine, s, requeue)
            s.append("")
        if machine in self.machines_with_final_state:
            s.append("  end:")
            s.append("    skip;")
        s.append("}")

    def _next_state(self, transition, s, indent="      "):
        if transition.target == "final":
            s.append(indent + "goto end;")
        else:
            s.append(indent + "goto {};".format(transition.target))

    def _effect(self, transition, s):
        for action in transition.effect:
            if action["name"] == "start_timer":
                s.append(
                    "           run Timer(queue, {}_c, {});".format(
                        action["args"][0], action["args"][0]
                    )
                )
            elif action["name"] == "stop_timer":
                s.append("           {}_c ! stop;".format(action["args"][0]))
            else:
                s.append("           /* {}() */".format(action["name"]))

    def _state_simple(self, state, machine, s, requeue):
        outgoing = []
        consumed = []
        for transition in machine._table.values():
            if transition.source == state:
                outgoing.append(transition)
                consumed.append(transition.trigger)
        consumed = set(consumed)
        discard = self.machine_to_triggers[machine._id] - consumed

        s.append("  {}:".format(state))
        s.append(
            "    if :: (queue ?? [{}]) ->".format("] || queue ?? [".join(consumed))
        )
        s.append("       do")

        for drop in discard:
            s.append("        :: discard({});".format(drop))
        for transition in outgoing:
            self._transition(transition, s, requeue)
        s.append("      od;")
        s.append("    fi;")

    def _state(self, state, machine, s, requeue):
        outgoing = []
        consumed = []
        for transition in machine.transitions:
            if transition.source == state:
                outgoing.append(transition)
                consumed.append(transition.trigger)
        consumed = set(consumed)
        discard = self.machine_to_triggers[machine._id] - consumed - deferred

        s.append("  {}:".format(state.name))
        s.append(
            "    if :: (queue ?? [{}]) ->".format("] || queue ?? [".join(consumed))
        )
        s.append("       do")
        for defer in state.defer:
            s.append("        :: save({});".format(defer))
        for drop in discard:
            s.append("        :: discard({});".format(drop))
        for transition in outgoing:
            self._transition(transition, s, requeue)
        s.append("      od;")
        s.append("    fi;")

    def _transition(self, transition, s, requeue):
        s.append("        :: queue ? {} -> atomic {{".format(transition.trigger))
        if requeue:
            s.append("           requeue();")
        self._effect(transition, s)
        self._next_state(transition, s)
        s.append("        }")


def to_promela(machines):
    """Experimental feature to export machines as Promela processes
    for model checking in Spin.
    """
    p = Promela(machines)
    return p.to_promela()
