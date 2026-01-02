from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()


class Agents:
    def __init__(self):
        self.__model = None

    def llm_setup(self, model=""):
        if not model:
            raise ValueError("please provide model name")

        open_router_api_key = os.getenv("OPEN_ROUTER_API_KEY")
        llm = ChatOpenAI(
            model=model,
            api_key=open_router_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.__model = model
        return llm

    def get_model(self):
        return self.__model
