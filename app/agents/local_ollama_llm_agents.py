from langchain_ollama.chat_models import ChatOllama


class Agents:
    def __init__(self):
        self.__model = ""

    def create_agentz(self, model=""):
        if not model:
            raise ValueError("Model name is required")
        self.__model = model
        llm = ChatOllama(
            model=self.__model,
            temperature=0.1,
            verbose=True,
        )

        return llm

    def get_model(self):
        return self.__model
