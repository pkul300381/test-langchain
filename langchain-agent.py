import os
import keyring
from dotenv import load_dotenv
from langchain_perplexity import ChatPerplexity

# Load environment variables from .env file as fallback
load_dotenv()

# --- Retrieve API Key Securely ---
# Try Keychain first (most secure), fall back to .env
SERVICE_NAME = "langchain-agent"
USERNAME = "perplexity"

PERPLEXITY_API_KEY = keyring.get_password(SERVICE_NAME, USERNAME)

# Fallback to .env file if Keychain is not set up
if not PERPLEXITY_API_KEY:
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError(
        "PERPLEXITY_API_KEY not found.\n"
        "Please set it using one of these methods:\n"
        "  1. Run: python3 setup_keychain.py (recommended - uses macOS Keychain)\n"
        "  2. Set PERPLEXITY_API_KEY in your .env file\n"
        "  3. Set PERPLEXITY_API_KEY environment variable"
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
