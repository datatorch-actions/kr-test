import os

from datatorch import get_input, agent, set_output
directory = os.path.dirname(os.path.abspath(__file__))
agent_dir = agent.directories().root
event = get_input("event")

print(event)
