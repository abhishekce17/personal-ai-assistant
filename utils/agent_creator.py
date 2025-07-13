from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from Tools.example_tools import tools


def agent_creator(enable_memory: bool, memory_instance=None, tools_list=[], llm=None):
    if enable_memory:
        memory = memory_instance if memory_instance is not None else MemorySaver()
        agent = create_react_agent(llm, tools=tools_list + tools, checkpointer=memory)
        print("Agent initialized successfully!\n")
        return agent
    else:
        agent = create_react_agent(llm, tools=tools_list + tools)
        print("Agent initialized successfully!\n")
        return agent
