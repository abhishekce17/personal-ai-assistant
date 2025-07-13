from utils.agent_creator import agent_creator
from langchain_openai import ChatOpenAI
from Tools.example_tools import tools
from dotenv import load_dotenv
import os

load_dotenv()


class Agents:
    def __init__(self, tools_list=[]):
        self.__tools_list = tools_list
        self.__model = None

    def create_agent(self, memory_instance, model="", enable_memory=False):
        if not model:
            raise ValueError("please provide model name")

        open_router_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        llm = ChatOpenAI(
            model=model,
            api_key=open_router_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        return agent_creator(
            enable_memory=enable_memory,
            memory_instance=memory_instance,
            tools_list=self.__tools_list,
            llm=llm,
        )

    def get_model(self):
        return self.__model
