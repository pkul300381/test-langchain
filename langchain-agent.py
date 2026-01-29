import os
from dotenv import load_dotenv
from langchain_perplexity import ChatPerplexity

# Load environment variables from .env file
load_dotenv()

# --- Retrieve API Key Securely ---
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError(
        "PERPLEXITY_API_KEY not found. Please set it in your .env file or environment variable."
    )

# LLM with Perplexity
llm = ChatPerplexity(
    api_key=PERPLEXITY_API_KEY,
    model="sonar",
    temperature=0
)

# Simple example - invoke the LLM directly
print("=" * 50)
print("Running agent with Perplexity API")
print("=" * 50)

response = llm.invoke("What is 87 * 45? And write a short poem about calculators.")
print("\nFINAL RESULT:")
print(response.content)
