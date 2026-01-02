import random
from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Define the State (The Shared Memory)
# We define a schema for our graph's memory using TypedDict.
class State(TypedDict):
    graph_state: str

# 2. Define the Nodes (The "Doers")
# Nodes are standard Python functions that take the current state, 
# perform an action, and return an update to the state.

def node_1(state):
    print("---Node 1---")
    # Appends " AGI" to the existing state string
    print("state at node_1: \n ", state)
    return {"graph_state": state['graph_state'] + " AGI"}

def node_2(state):
    print("---Node 2---")
    print("state at node_2: \n ", state)
    # Appends " Achieved!"
    return {"graph_state": state['graph_state'] + " Achieved!"}

def node_3(state):
    print("---Node 3---")
    print("state at node_3: \n ", state)
    # Appends " Not Achieved :("
    return {"graph_state": state['graph_state'] + " Not Achieved :("}

# 3. Define the Edges (The "Decision Makers")
# This function decides which node to visit next based on logic.
def decide_mood(state) -> Literal["node_2", "node_3"]:
    # Simulating a decision with a random 50/50 split
    if random.random() < 0.5:
        return "node_2"
    return "node_3"

# 4. Construct the Graph
# Initialize the graph builder with our State schema
builder = StateGraph(State)

# print("builder: \n ", builder)

# Add nodes to the graph
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# Define the flow (Edges)
# Start -> Node 1
builder.add_edge(START, "node_1")

# Node 1 -> (Conditional Decision) -> Node 2 OR Node 3
builder.add_conditional_edges("node_1", decide_mood)

# Node 2 & Node 3 -> End
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)

# 5. Compile the Graph
graph = builder.compile()

# 6. Execute (Invoke)
# We pass an initial state to start the workflow.


#result = graph.invoke({"graph_state": "Has AGI been achieved?"})
#print(result)

state = State(graph_state="Has AGI been achieved?")
result = graph.invoke(state)
print(result)