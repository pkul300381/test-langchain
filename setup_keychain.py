#!/usr/bin/env python3
"""
Setup script to securely store Perplexity API key in macOS Keychain.

Usage:
    python3 setup_keychain.py
    
This will prompt you to enter your Perplexity API key, which will be stored
in your system's secure Keychain and retrieved by the agent.
"""

import keyring
import getpass
from pathlib import Path

SERVICE_NAME = "langchain-agent"
USERNAME = "perplexity"


def setup_keychain():
    """Securely store API key in macOS Keychain."""
    print("=" * 60)
    print("Perplexity API Key - Secure Keychain Setup")
    print("=" * 60)
    print()
    
    # Get API key from user
    api_key = getpass.getpass(
        "Enter your Perplexity API key (input will be hidden): "
    )
    
    if not api_key:
        print("❌ Error: API key cannot be empty")
        return False
    
    try:
        # Store in keychain
        keyring.set_password(SERVICE_NAME, USERNAME, api_key)
        print()
        print("✅ Successfully stored API key in macOS Keychain!")
        print(f"   Service: {SERVICE_NAME}")
        print(f"   Username: {USERNAME}")
        print()
        print("You can now run: python3 langchain-agent.py")
        return True
    except Exception as e:
        print(f"❌ Error storing in Keychain: {e}")
        return False


def verify_setup():
    """Verify that the API key is stored in Keychain."""
    try:
        api_key = keyring.get_password(SERVICE_NAME, USERNAME)
        if api_key:
            print("✅ API key found in Keychain")
            return True
        else:
            print("❌ API key not found in Keychain")
            return False
    except Exception as e:
        print(f"❌ Error verifying Keychain: {e}")
        return False


if __name__ == "__main__":
    # setup_keychain() 
    verify_setup()
