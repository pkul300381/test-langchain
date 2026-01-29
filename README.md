# LangChain Perplexity Agent

A secure LangChain agent configured to use the Perplexity API with macOS Keychain integration for credential management.

## Security Features

This project implements multiple layers of secure credential management:

### 1. **macOS Keychain (Recommended)** 🔐
Your API key is stored in your system's secure Keychain, encrypted and managed by macOS.

### 2. **Environment Variables (.env fallback)**
If Keychain is not available, credentials can be loaded from a `.env` file (excluded from git).

### 3. **No hardcoded secrets**
API keys are never stored in code or committed to version control.

## Setup Instructions

### First Time Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Store API key in Keychain (recommended):**
   ```bash
   python3 setup_keychain.py
   ```
   This will prompt you to enter your Perplexity API key, which will be securely stored in macOS Keychain.

3. **Run the agent:**
   ```bash
   python3 langchain-agent.py
   ```

### Alternative: Using .env file

If you prefer to use environment variables instead of Keychain:

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   PERPLEXITY_API_KEY=your_api_key_here
   ```

3. Run the agent:
   ```bash
   python3 langchain-agent.py
   ```

**Important:** Never commit `.env` to version control. It's already in `.gitignore`.

## Credential Retrieval Priority

The agent retrieves credentials in this order:

1. **macOS Keychain** (if set up via `setup_keychain.py`)
2. **.env file** (if `PERPLEXITY_API_KEY` is set)
3. **Environment variable** (if `PERPLEXITY_API_KEY` is set in shell)

## Managing Credentials

### View stored Keychain credentials (macOS):
```bash
security dump-keychain | grep langchain-agent
```

### Update Keychain credentials:
```bash
python3 setup_keychain.py
```

### Delete Keychain credentials:
```bash
security delete-generic-password -s "langchain-agent" -a "perplexity"
```

## Files

- `langchain-agent.py` - Main agent script
- `setup_keychain.py` - Interactive script to store API key in Keychain
- `.env.example` - Template for environment variables
- `.env` - Environment file (git-ignored, created by user)
- `.gitignore` - Excludes sensitive files from version control

## Getting API Keys

- **Perplexity API**: https://www.perplexity.ai/

## Security Best Practices

✅ **Do:**
- Use macOS Keychain for production/personal machines
- Use environment variables for CI/CD pipelines
- Keep `.env` out of version control
- Rotate API keys regularly

❌ **Don't:**
- Commit `.env` files to git
- Hardcode secrets in code
- Share API keys via email or chat
- Use the same key across multiple projects

## Troubleshooting

### "PERPLEXITY_API_KEY not found"
- Run `python3 setup_keychain.py` to store key in Keychain, OR
- Create `.env` file with your API key

### Keychain not working
- Ensure you're on macOS
- Try the `.env` file fallback method
- Check that `keyring` is installed: `pip list | grep keyring`

## License

MIT