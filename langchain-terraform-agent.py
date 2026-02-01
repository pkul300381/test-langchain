import os
import sys
import logging
from dotenv import load_dotenv
from langchain_classic.agents import initialize_agent, AgentType
from langchain_classic.memory import ConversationBufferMemory
from llm_config import select_llm_interactive, select_credential_source_interactive, initialize_llm
from terraform_tools import get_terraform_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('.agent-session.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Log session start
logger.info("=" * 80)
logger.info("LangChain Terraform AWS Agent Session Started")
logger.info("=" * 80)

print("=" * 60)
print("LangChain Terraform AWS Agent")
print("=" * 60)
print()

# Check if LLM is specified via environment variable
llm_provider = os.getenv("LLM_PROVIDER", "").lower()

if llm_provider:
    print(f"[INFO] Using LLM provider from environment: {llm_provider}")
    logger.info(f"LLM Provider: {llm_provider.upper()} (from LLM_PROVIDER environment variable)")
else:
    # Ask user to select LLM
    llm_provider = select_llm_interactive()
    logger.info(f"LLM Provider: {llm_provider.upper()} (selected interactively)")

print(f"\n[INFO] Initializing {llm_provider.upper()}...")

try:
    # Select credential source
    credential_source = select_credential_source_interactive()

    # Initialize the selected LLM
    llm = initialize_llm(llm_provider, temperature=0, preferred_source=credential_source)
    print(f"✅ {llm_provider.upper()} initialized successfully!")
    logger.info(f"LLM initialization successful - Provider: {llm_provider.upper()}")
except Exception as e:
    print(f"\n❌ Error initializing {llm_provider}: {e}")
    logger.error(f"Failed to initialize LLM provider '{llm_provider}': {str(e)}", exc_info=True)
    sys.exit(1)

# Get Terraform tools
tools = get_terraform_tools()
logger.info("Terraform tools loaded")

# Set up memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Initialize the agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory
)
logger.info("Agent initialized with CHAT_CONVERSATIONAL_REACT_DESCRIPTION type")

print("\n" + "=" * 60)
print("Terraform Agent - Ready to deploy infrastructure on AWS")
print("=" * 60)
print("Example tasks:")
print("  'Create a VPC in us-east-1'")
print("  'Deploy an S3 bucket with a specific name'")
print("  'Show me the current terraform plan'")
print("=" * 60)
print()

while True:
    try:
        user_query = input("You: ").strip()

        if user_query.lower() in ["quit", "exit", "q", "x"]:
            logger.info("Agent session ended by user (exit command)")
            print("\n👋 Goodbye!")
            break

        if not user_query:
            continue

        logger.info(f"Processing user query: {user_query}")
        print("\n🔄 Processing...")
        response = agent.run(input=user_query)

        print("\nAgent:")
        print("-" * 60)
        print(response)
        print()
        logger.info("Response generated and displayed")

    except KeyboardInterrupt:
        logger.info("Agent session interrupted by user (Ctrl+C)")
        print("\n\n👋 Interrupted. Goodbye!")
        break
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
