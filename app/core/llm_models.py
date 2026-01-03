from enum import Enum


class OpenRouter_Agents(str, Enum):
    DEEPSEEK_R1 = "deepseek/deepseek-r1-0528-qwen3-8b:free"  # no tool
    MISTRAL_24B = "mistralai/mistral-small-3.2-24b-instruct:free"
    QWEN3_235B = "qwen/qwen3-235b-a22b:free"
    QWEN3_32B = "qwen/qwen3-32b:free"
    GOOGLE_GEMMA_27B = "google/gemma-3-27b-it:free"
    DEEPSEEK_V3 = "deepseek/deepseek-chat-v3-0324:free"
    MINIMAX_EXTENDED = "minimax/minimax-m1:extended"
    GEMINI25_FLASH = "google/gemini-2.0-flash-exp:free"


class Cohere_Agents(str, Enum):
    COMMAND_A = "command-a-03-2025"


class Ollama_LLM(str, Enum):
    LLAMA3_1 = "llama3.1:8b"

class Groq_Cloud(str, Enum):
    LLAMA3_3_70B_VERSATILE = "llama-3.3-70b-versatile"

