def _print_action(action):
    s = []
    s.append(action["name"])
    if action["event_args"]:
        s.append("(*)")
    else:
        s.append("(")
        first = True
        for arg in action["args"]:
            if first:
                s.append("{}".format(arg))
                first = False
            else:
                s.append(", {}".format(arg))
        s.append(")")
    return "".join(s)


def _print_state(state):
    s = []
    s.append(
        '{} [shape=plaintext margin=0 label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" STYLE="ROUNDED"><TR><TD><B>{}</B></TD></TR>\n'.format(
            state.name, state.name
        )
    )
    if state.entry or state.exit or state.internal or state.defer:
        s.append("<HR/>")
        s.append('<TR><TD ALIGN="LEFT">')
        for entry in state.entry:
            s.append("entry / {}<BR/>".format(_print_action(entry)))
        for internal in state.internal:
            s.append(
                "{} / {}<BR/>".format(internal["trigger"], internal["effect_string"])
            )
        for defer in state.defer:
            s.append("{} / {}<BR/>".format(defer, "defer"))
        for exit in state.exit:
            s.append("exit / {}<BR/>".format(_print_action(exit)))
        s.append("</TD></TR>")
    s.append("</TABLE>>];")
    return "".join(s)


def _print_transition(t, counter):
    s = []
    label = ""
    if t.trigger:
        label = label + t.trigger
    if t.effect:
        label = label + " /"
        if t.trigger:
            label = label + "\\n"
        for effect in t.effect:
            label = label + "{};\\n".format(_print_action(effect))
    if hasattr(t, "function"):  # we have a compound transition
        decision_name = "d_{}".format(counter)
        s.append(
            '{} -> {} [label="{}()"]\n'.format(
                t.source, decision_name, t.function.__name__
            )
        )
        s.append(
            '{} [shape=diamond, style=filled, label="", fillcolor=black, height=0.3, width=0.3, fixedsize=true]\n'.format(
                decision_name
            )
        )
        if hasattr(t, "targets"):
            for target in t.targets:
                s.append("{} -> {}\n".format(decision_name, target))
    else:
        if t.target == "final":
            s.append('{} -> f{} [label=" {}"]\n'.format(t.source, counter, label))
        else:
            s.append('{} -> {} [label=" {}"]\n'.format(t.source, t.target, label))
    return "".join(s)


def to_graphviz(machine):
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
    s.append("digraph G {\n")
    s.append("node [shape=box style=rounded fontname=Helvetica];\n")
    s.append("edge [ fontname=Helvetica ];\n")
    # initial state
    s.append("initial [shape=point width=0.2];\n")
    # final states
    counter = 1
    for t_id in machine._table:
        transition = machine._table[t_id]
        if not transition.internal:
            if transition.target == "final":
                s.append(
                    'f{} [shape=doublecircle width=0.1 label="" style=filled fillcolor=black];\n'.format(
                        counter
                    )
                )
            counter = counter + 1

    for state_name in machine._states:
        s.append(_print_state(machine._states[state_name]))
    # initial transition
    counter = 0
    s.append(_print_transition(machine._initial_transition, counter))
    counter = 1
    for t_id in machine._table:
        transition = machine._table[t_id]
        if not transition.internal:
            s.append(_print_transition(transition, counter))
            counter = counter + 1
    s.append("}")
    return "".join(s)
