import os

from datatorch import get_input, agent, set_output
directory = os.path.dirname(os.path.abspath(__file__))
agent_dir = agent.directories().root

dt_fileId = get_input("fileId")
command = get_input("command")
projectId = get_input("projectId")

set_output("returnText",event)
