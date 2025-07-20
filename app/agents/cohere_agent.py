from langchain_cohere import ChatCohere
from dotenv import load_dotenv
import os

load_dotenv()


class Agents:
    def __init__(self):
        self.__model = "command-a-03-2025"
        pass

    def llm_setup(
        self,
        model="",
    ):
        if not model:
            raise ValueError("Please provide model name")
        self.__model = model
        cohere_api_key = os.getenv("COHERE_API_KEY")
        llm = ChatCohere(
            cohere_api_key=cohere_api_key,
            model=self.__model,
            temperature=0,
        )
        return llm

    def get_model(self):
        return self.__model
