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
    # All-Rounder
    LLAMA_4_SCOUT_17B_16E_INSTRUCT = "meta-llama/llama-4-scout-17b-16e-instruct"
    LLAMA_3_3_70B_VERSATILE = "llama-3.3-70b-versatile"
    OPENAI_GPT_OSS_120B = "openai/gpt-oss-120b"
    KIMI_K2_INSTRUCT = "moonshotai/kimi-k2-instruct"
    KIMI_K2_INSTRUCT_0905 = "moonshotai/kimi-k2-instruct-0905"
    LLAMA_4_MAVERICK_17B_128E_INSTRUCT = "meta-llama/llama-4-maverick-17b-128e-instruct"

    # Single Tool Use & Sub-Agents
    QWEN_3_32B_ORCHESTRATOR = "qwen/qwen3-32b"
    LLAMA_3_1_8B_INSTANT = "llama-3.1-8b-instant"
    OPENAI_GPT_OSS_20B = "openai/gpt-oss-20b"
    GROQ_COMPOUND = "groq/compound"
    GROQ_COMPOUND_MINI = "groq/compound-mini"
    ALLAM_2_7B = "allam-2-7b"
    ORPHEUS_ARABIC_SAUDI = "canopylabs/orpheus-arabic-saudi"
    ORPHEUS_V1_ENGLISH = "canopylabs/orpheus-v1-english"
    WHISPER_LARGE_V3 = "whisper-large-v3"

    # Security & Guardrail
    LLAMA_GUARD_4_12B = "meta-llama/llama-guard-4-12b"
    LLAMA_PROMPT_GUARD_2_86M = "meta-llama/llama-prompt-guard-2-86m"
    LLAMA_PROMPT_GUARD_2_22M = "meta-llama/llama-prompt-guard-2-22m"
    OPENAI_GPT_OSS_SAFEGUARD_20B = "openai/gpt-oss-safeguard-20b"

