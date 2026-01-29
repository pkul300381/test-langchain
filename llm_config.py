"""
LLM Configuration Module

Manages different LLM providers and their API keys.
Supports: OpenAI, Gemini, Claude, Perplexity, Ollama
"""

import os
import keyring
from typing import Optional

# LLM Provider configurations
SUPPORTED_LLMS = {
    "perplexity": {
        "name": "Perplexity (Sonar)",
        "package": "langchain_perplexity",
        "class": "ChatPerplexity",
        "default_model": "sonar",
        "requires_api_key": True,
        "env_var": "PERPLEXITY_API_KEY",
    },
    "openai": {
        "name": "OpenAI (GPT-4)",
        "package": "langchain_openai",
        "class": "ChatOpenAI",
        "default_model": "gpt-4o-mini",
        "requires_api_key": True,
        "env_var": "OPENAI_API_KEY",
    },
    "gemini": {
        "name": "Google Gemini",
        "package": "langchain_google_genai",
        "class": "ChatGoogleGenerativeAI",
        "default_model": "gemini-pro",
        "requires_api_key": True,
        "env_var": "GOOGLE_API_KEY",
    },
    "claude": {
        "name": "Anthropic Claude",
        "package": "langchain_anthropic",
        "class": "ChatAnthropic",
        "default_model": "claude-3-5-sonnet-20241022",
        "requires_api_key": True,
        "env_var": "ANTHROPIC_API_KEY",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "package": "langchain_ollama",
        "class": "ChatOllama",
        "default_model": "llama2",
        "requires_api_key": False,
        "env_var": None,
    },
}


def get_api_key(provider: str, service_name: str = "langchain-agent") -> Optional[str]:
    """
    Retrieve API key for a provider in order of priority:
    1. Local keyring
    2. Azure KeyVault
    3. AWS Secrets Manager
    4. .env file
    5. Environment variable
    """
    from dotenv import load_dotenv
    
    load_dotenv()
    
    if provider not in SUPPORTED_LLMS:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    config = SUPPORTED_LLMS[provider]
    env_var = config["env_var"]
    secret_name = f"{provider}-api-key"
    
    api_key = None
    
    # 1. Try local keyring
    try:
        api_key = keyring.get_password(service_name, provider)
        if api_key:
            return api_key
    except:
        pass
    
    # 2. Try Azure KeyVault
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient
        
        keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
        if keyvault_url:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=keyvault_url, credential=credential)
            secret = client.get_secret(secret_name)
            if secret:
                return secret.value
    except:
        pass
    
    # 3. Try AWS Secrets Manager
    try:
        import boto3
        
        aws_region = os.getenv("AWS_REGION")
        if aws_region:
            client = boto3.client("secretsmanager", region_name=aws_region)
            secret = client.get_secret_value(SecretId=secret_name)
            api_key = secret.get("SecretString")
            if api_key:
                return api_key
    except:
        pass
    
    # 4. Try .env file
    if env_var:
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
    
    # 5. Try environment variable (already covered above, but be explicit)
    if env_var:
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
    
    return None


def initialize_llm(provider: str, model: Optional[str] = None, **kwargs):
    """
    Initialize and return an LLM instance for the given provider.
    
    Args:
        provider: LLM provider name (perplexity, openai, gemini, claude, ollama)
        model: Model name (optional, uses default if not specified)
        **kwargs: Additional arguments to pass to the LLM constructor
    
    Returns:
        Initialized LLM instance
    """
    if provider not in SUPPORTED_LLMS:
        raise ValueError(f"Unsupported LLM provider: {provider}. Choose from: {list(SUPPORTED_LLMS.keys())}")
    
    config = SUPPORTED_LLMS[provider]
    model = model or config["default_model"]
    
    # Get API key if required
    if config["requires_api_key"]:
        api_key = get_api_key(provider)
        if not api_key:
            raise ValueError(
                f"API key for {config['name']} not found.\n"
                f"Please set {config['env_var']} or run: python3 setup_keychain.py"
            )
    
    # Import and instantiate the LLM class
    module = __import__(config["package"], fromlist=[config["class"]])
    llm_class = getattr(module, config["class"])
    
    # Build initialization parameters
    llm_params = {"model": model, **kwargs}
    
    # Add API key if required
    if config["requires_api_key"]:
        api_key = get_api_key(provider)
        if provider == "perplexity":
            llm_params["api_key"] = api_key
        elif provider == "openai":
            llm_params["api_key"] = api_key
        elif provider == "gemini":
            llm_params["api_key"] = api_key
        elif provider == "claude":
            llm_params["api_key"] = api_key
    
    # Handle Ollama's special base_url parameter
    if provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm_params["base_url"] = ollama_base_url
    
    llm = llm_class(**llm_params)
    return llm


def list_available_llms():
    """Print available LLM providers."""
    print("\n" + "=" * 60)
    print("Available LLM Providers")
    print("=" * 60)
    
    for i, (provider_key, config) in enumerate(SUPPORTED_LLMS.items(), 1):
        key_status = "✓" if config["requires_api_key"] else "✓ (No key needed)"
        print(f"{i}. {config['name']}")
        print(f"   Provider: {provider_key}")
        print(f"   Default Model: {config['default_model']}")
        print(f"   API Key Required: {key_status}")
        if config["env_var"]:
            print(f"   Env Variable: {config['env_var']}")
        print()


def select_llm_interactive():
    """Interactively select an LLM provider."""
    list_available_llms()
    
    providers = list(SUPPORTED_LLMS.keys())
    
    while True:
        choice = input("Enter LLM provider number or name (1-5): ").strip().lower()
        
        # Check if it's a number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(providers):
                return providers[idx]
        except ValueError:
            pass
        
        # Check if it's a provider name
        if choice in providers:
            return choice
        
        print("❌ Invalid choice. Please try again.")
