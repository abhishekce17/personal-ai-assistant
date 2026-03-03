# Comprehensive GroqCloud Model Categorization

## 1. All-Rounder (Text + Image + Coding & Software Architecture)

_These models are your heavy lifters for complex system design, deep reasoning, and multimodal understanding._

- **`meta-llama/llama-4-scout-17b-16e-instruct`**
  - **Category:** Multimodal Architecture & Coding.
  - **Role:** The only vision-capable model in the list. Best for uploading UI wireframes, architecture diagrams, or screenshots of bugs, and generating corresponding code or system analysis.
- **`llama-3.3-70b-versatile`**
  - **Category:** Deep Reasoning & System Design (Text Only).
  - **Role:** Excellent for rigorous software architecture, complex logic, and deep technical drafting.
- **`openai/gpt-oss-120b`**
  - **Category:** Advanced Architecture (Text Only).
  - **Role:** A massive parameter model suited for highly complex, multi-step system design and robust coding tasks.
- **`moonshotai/kimi-k2-instruct` & `moonshotai/kimi-k2-instruct-0905`**
  - **Category:** Long-Context All-Rounder (Text Only).
  - **Role:** Kimi models are generally known for handling massive context windows. Great for feeding in entire codebases or extensive documentation for architectural reviews.
- **`meta-llama/llama-4-maverick-17b-128e-instruct`**
  - **Category:** High-Efficiency Coder (Text Only).
  - **Role:** A dense Mixture-of-Experts model. Excellent for fast, highly capable code generation and logic problem solving without the overhead of a 70B+ model.

## 2. Single Tool Use & Sub-Agents (Atomic Tasks)

_These models are highly specialized, extremely fast, or designed specifically to act as routing nodes, filters, or single-task executors within a larger backend._

- **`qwen/qwen3-32b`**
  - **Category:** Tool Orchestrator.
  - **Role:** Extremely reliable for JSON generation, function calling, and deciding which external APIs or databases to query.
- **`llama-3.1-8b-instant`**
  - **Category:** Fast Triage & Routing.
  - **Role:** The perfect entry-point agent to quickly classify user intent and route prompts to heavier models.
- **`openai/gpt-oss-20b`**
  - **Category:** Mid-Tier Processor.
  - **Role:** A solid balance of speed and capability for intermediate tasks like standardizing text or summarizing medium-length logs.
- **`groq/compound` & `groq/compound-mini`**
  - **Category:** Utility Nodes.
  - **Role:** High-throughput models best for background atomic tasks, metadata parsing, or basic text transformations.
- **`allam-2-7b`**
  - **Category:** Regional/Language Sub-Agent.
  - **Role:** Specialized lightweight model, typically optimized for specific linguistic tasks (like Arabic) or regional localization.
- **`canopylabs/orpheus-arabic-saudi` & `canopylabs/orpheus-v1-english`**
  - **Category:** Specialized Domain Agents.
  - **Role:** Likely fine-tuned for specific domain workflows, regional dialects, or specialized text generation tasks.
- **`whisper-large-v3`**
  - **Category:** Audio Processing Node.
  - **Role:** Dedicated entirely to transcribing speech-to-text.

### Security & Guardrail Sub-Agents

_Run these in parallel or as middleware to sanitize inputs and outputs._

- **`meta-llama/llama-guard-4-12b`** (Heavy duty content moderation)
- **`meta-llama/llama-prompt-guard-2-86m`** (Prompt injection detection)
- **`meta-llama/llama-prompt-guard-2-22m`** (Ultra-light prompt injection detection)
- **`openai/gpt-oss-safeguard-20b`** (Advanced safety and alignment filtering)

## 3. Image Only

- **`meta-llama/llama-4-scout-17b-16e-instruct`**
  - **Category:** Vision Extractor.
  - **Role:** As the sole model supporting vision, it acts as the "eyes" of the system. You can use it strictly to extract rich text descriptions from images, and then pipe that text output to a smarter, text-only model (like `gpt-oss-120b`) for the actual software architecture decisions.
