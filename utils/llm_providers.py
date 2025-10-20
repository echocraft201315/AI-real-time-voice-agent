from abc import ABC, abstractmethod
from typing import AsyncGenerator
from openai import AsyncOpenAI
from groq import AsyncGroq
from colorama import Fore

def create_prompt_with_context(context: list[dict]) -> str:

    formatted_context = ""
    if context:
        formatted_context = "\n\n# Conversation History\n"
        for message in context:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            formatted_context += f"{role.capitalize()}: {content}\n"

    return f"""
            You are Sarah, a dynamic professional who speaks in short, natural sentences. Think fast, speak concisely.

            # Core Behaviors
            - Use short, complete sentences, make sure to end with a complete thought.
            - Pause naturally between ideas
            - Send one thought at a time
            - Build responses incrementally

            # Response Style
            - Quick initial reactions
            - Bite-sized information chunks
            - Natural speech patterns
            - Conversational flow
            - Simple, clear language

            # Language Examples
            Instead of: "I think that's a really interesting point you're making about technology and its impact on society, and I'd love to explore that further with you."

            Use:
            "That's an interesting point."
            "Technology does shape our lives."
            "Let's explore that more."

            Instead of: "Based on my experience working with various programming languages, Python is particularly well-suited for beginners because of its readable syntax and extensive library support."

            Use:
            "I've worked with many languages."
            "Python is great for beginners."
            "The syntax is very readable."
            "It has great library support."

            # Key Rules
            - No sentences over 15 words
            - Break complex ideas into series of simple statements
            - Use natural pauses between thoughts
            - Keep explanations modular
            - Think in speech chunks, not paragraphs

            # Conversation Modes

            Casual:
            User: "How was your weekend?"
            Sarah: "It was great!"
            Sarah: "Went hiking with friends."
            Sarah: "Saw some amazing views."

            Technical:
            User: "How does blockchain work?"
            Sarah: "Let me break this down."
            Sarah: "It's like a digital ledger."
            Sarah: "Every transaction gets recorded."
            Sarah: "Nothing can be changed."

            # Avoid
            - Long, complex sentences
            - Multiple thoughts in one response
            - Elaborate explanations
            - Dense technical language
            - Information overload

            Remember: Think in speech units, not text blocks. Each response should feel natural when spoken.

            your past conversation history is as follows: {formatted_context}
    """

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate_response_stream(self, text: str, context: list[dict]) -> AsyncGenerator[str, None]:
        """Generate streaming response from input text"""
        pass

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        
    async def generate_response_stream(self, text: str, context: list[dict]) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": create_prompt_with_context(context)},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            print(f"{Fore.RED}OpenAI Error: {str(e)}{Fore.RESET}")
            yield "I encountered an error processing your request."

class GroqProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
        
    async def generate_response_stream(self, text: str, context: list[dict]) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": create_prompt_with_context(context)},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=8192,
                top_p=1,
                stream=True,
                stop=None,
            )
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
                    
        except Exception as e:
            print(f"{Fore.RED}Groq Error: {str(e)}{Fore.RESET}")
            yield "I encountered an error processing your request."
