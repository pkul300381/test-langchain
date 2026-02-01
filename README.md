# LangChain Multi-LLM & Terraform Agent

An interactive LangChain agent ecosystem with support for multiple LLM providers, AWS infrastructure management via Terraform, and exposure through MCP and REST API.

## Core Features

### 🤖 Multi-LLM Chat Agent
- **Multiple Providers** - Support for Perplexity, OpenAI, Gemini, Claude, and Ollama.
- **Multi-turn conversation** - Maintains context across queries.
- **Interactive CLI** - Ask questions and maintain conversation history.

### 🏗️ Terraform AWS Agent
- **Infrastructure as Code** - Deploy AWS resources using natural language.
- **Automated Workflows** - Handles `terraform init`, `plan`, `apply`, and `destroy`.
- **AWS Integration** - Specifically designed for AWS infrastructure tasks.

### 🌐 Multiple Interfaces
1. **Interactive CLIs** - `langchain-agent.py` for chat, `langchain-terraform-agent.py` for infrastructure.
2. **REST API** - FastAPI-based server in `api_server.py`.
3. **MCP Server** - Model Context Protocol server in `mcp_server.py`.

### 🔐 Secure Credential Management
- **Local System Keyring** (macOS Keychain, Windows Credential Manager, Linux Secret Service).
- **Azure KeyVault** (cloud-based, cross-platform).
- **AWS Secrets Manager** (cloud-based).
- **Environment Variables** (.env fallback).

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   ```bash
   python3 setup_keychain.py
   ```
   Follow the prompts to store your API keys in your preferred location.

3. **Install Terraform and AWS CLI:**
   Ensure you have `terraform` and `aws` CLI tools installed and configured in your PATH.

## Usage

### 💬 General Chat Agent
```bash
python3 langchain-agent.py
```

### ☁️ Terraform AWS Agent
```bash
python3 langchain-terraform-agent.py
```
Example queries:
- "Create a VPC in us-east-1"
- "Deploy an S3 bucket named my-app-data"
- "Show me the current terraform plan"

### 🚀 API Server
```bash
python3 api_server.py
```
The API will be available at `http://localhost:8000`. You can use the `/chat` endpoint to interact with the agent.

### 🔌 MCP Server
```bash
python3 mcp_server.py
```
This starts the FastMCP server, which can be used by MCP-compatible clients to execute terraform tools.

## Logging
All components now feature comprehensive logging:
- General logs: `.agent-session.log`
- API logs: `.api-server.log`
- MCP logs: `.mcp-server.log`

## Dependencies
Major dependencies include:
- `langchain`, `langchain-core`, `langchain-community`, `langchain-classic`
- `fastapi`, `uvicorn`
- `mcp`
- `boto3`, `keyring`, `python-dotenv`

## Security Best Practices
- Use secure credential storage (Keyring, KeyVault, or Secrets Manager) instead of `.env` files for production.
- Never commit `.env` files or hardcoded secrets.
- Use IAM roles or service principals for cloud authentication.

## License
MIT
