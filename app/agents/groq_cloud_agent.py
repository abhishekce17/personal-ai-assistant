from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()


class Agents:
    def __init__(self):
        self.__model = None

    def llm_setup(self, model=""):
        if not model:
            raise ValueError("please provide model name")

        groq_cloud_api_key = os.getenv("GROQ_CLOUD_API_KEY")
        llm = ChatGroq(
            model_name=model,
            api_key=groq_cloud_api_key,
            temperature=0.7
        )

        self.__model = model
        return llm

    def get_model(self):
        return self.__model
