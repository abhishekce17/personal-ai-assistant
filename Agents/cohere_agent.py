from utils.agent_creator import agent_creator
from langchain_cohere import ChatCohere
from dotenv import load_dotenv
import os

load_dotenv()


class Agents:
    def __init__(self, tools_list=[]):
        self.__tools_list = tools_list
        self.__model = "command-a-03-2025"
        pass

    def create_agent(self, memory_instance, model="", enable_memory=False):
        if not model:
            raise ValueError("Please provide model name")
        self.__model = model
        cohere_api_key = os.getenv("COHERE_API_KEY")
        llm = ChatCohere(
            cohere_api_key=cohere_api_key,
            model=self.__model,
            temperature=0,
        )
        return agent_creator(
            enable_memory=enable_memory,
            memory_instance=memory_instance,
            tools_list=self.__tools_list,
            llm=llm,
        )

    def get_model(self):
        return self.__model
