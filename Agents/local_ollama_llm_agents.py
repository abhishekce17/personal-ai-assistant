from langchain_ollama.chat_models import ChatOllama
from utils.agent_creator import agent_creator


class Agents:
    def __init__(self, tools_list=[]):
        self.__tools_list = tools_list
        self.__model = ""

    def create_agent(self, memory_instance, model="", enable_memory=False):
        if not model:
            raise ValueError("Model name is required")
        self.__model = model
        llm = ChatOllama(
            model=self.__model,
            temperature=0.1,
            verbose=True,
        )

        return agent_creator(
            enable_memory=enable_memory,
            memory_instance=memory_instance,
            tools_list=self.__tools_list,
            llm=llm,
        )

    def get_model(self):
        return self.__model
