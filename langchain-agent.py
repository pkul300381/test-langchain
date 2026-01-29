import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from llm_config import select_llm_interactive, initialize_llm

# Load environment variables
load_dotenv()

# Determine which LLM to use
print("=" * 60)
print("LangChain Multi-LLM Agent")
print("=" * 60)
print()

# Check if LLM is specified via environment variable
llm_provider = os.getenv("LLM_PROVIDER", "").lower()

if llm_provider:
    print(f"[INFO] Using LLM provider from environment: {llm_provider}")
else:
    # Ask user to select LLM
    llm_provider = select_llm_interactive()

print(f"\n[INFO] Initializing {llm_provider.upper()}...")

try:
    # Initialize the selected LLM
    llm = initialize_llm(llm_provider, temperature=0)
    print(f"✅ {llm_provider.upper()} initialized successfully!\n")
except Exception as e:
    print(f"\n❌ Error initializing {llm_provider}: {e}")
    sys.exit(1)

# Interactive query loop with conversation history
print("=" * 60)
print("Conversational Agent - Type 'help' for commands")
print("=" * 60)
print("Commands:")
print("  quit/exit/q/x  - Exit the agent")
print("  clear          - Reset conversation history")
print("  help           - Show this help message")
print("=" * 60)
print()

# Store conversation history
conversation_history = []

while True:
    try:
        user_query = input("You: ").strip()
        
        # Check for exit commands
        if user_query.lower() in ["quit", "exit", "q", "x"]:
            print("\n👋 Goodbye!")
            break
        
        # Check for help command
        if user_query.lower() == "help":
            print("\nCommands:")
            print("  quit/exit/q/x  - Exit the agent")
            print("  clear          - Reset conversation history")
            print("  help           - Show this help message")
            print()
            continue
        
        # Check for clear history command
        if user_query.lower() == "clear":
            conversation_history = []
            print("✅ Conversation history cleared\n")
            continue
        
        if not user_query:
            print("❌ Error: Query cannot be empty\n")
            continue
        
        # Add user message to history
        conversation_history.append(HumanMessage(content=user_query))
        
        print("\n🔄 Processing your query...")
        print("-" * 60)
        
        # Invoke with full conversation history
        response = llm.invoke(conversation_history)
        
        # Add AI response to history
        conversation_history.append(AIMessage(content=response.content))
        
        print()
        print("Agent:")
        print("-" * 60)
        print(response.content)
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
