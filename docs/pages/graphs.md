# Graphs with Graphviz

You can automatically generate state machine graphs from STMPY state machines, using the [Graphviz](https://graphviz.gitlab.io) tool.


## Installing Graphviz

To learn more about Graphviz and how to install it, visit [https://graphviz.gitlab.io](https://graphviz.gitlab.io).

In addition, install the Python library for Graphviz:

    pip install graphviz



## Using Graphviz on the Command Line

Write the graph file with the following code:

    with open("graph.gv", "w") as file:
        print(stmpy.get_graphviz_dot(stm), file=file)

The format is the dot format for Graphviz, and can be directly used as input to the Graphviz command line tool:

    dot -Tsvg graph.gv -o graph.svg


## Display in Jupyter Notebook

In a notebook, build a stmpy.Machine. Then, declare a cell with the following content:

    from graphviz import Source
    src = Source(stmpy.get_graphviz_dot(stm))
    src
