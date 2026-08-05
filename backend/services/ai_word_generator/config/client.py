import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from openai import OpenAI
from langchain_groq import ChatGroq

load_dotenv()

def get_gemini_client():
    """Returns a configured Gemini LLM client"""
    # return ChatGoogleGenerativeAI(
    #     model="gemini-1.5-flash",
    #     google_api_key=os.getenv("GEMINI_API_KEY"),
    #     temperature=0.7,
    # )

    # return OpenAI(
    #     base_url="https://models.inference.ai.azure.com",
    #     api_key=os.environ.get("GITHUB_TOKEN"),
    # )

    return ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.9,
    max_tokens=2500,
    api_key=os.getenv("GROQ_API_KEY"),
    max_retries=2,
    verbose=True,
)
