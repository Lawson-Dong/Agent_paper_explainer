#!/usr/bin/env python3
"""
Test script to verify DeepSeek API connectivity
"""
from config import DEEPSEEK_API_KEY
from langchain_deepseek import ChatDeepSeek
from langchain_openai import OpenAIEmbeddings

def test_deepseek_chat():
    """Test DeepSeek chat model"""
    try:
        llm = ChatDeepSeek(
            model="deepseek-chat",
            api_key=DEEPSEEK_API_KEY,
            temperature=0
        )
        response = llm.invoke("Hello, can you respond with just 'DeepSeek test successful'?")
        print("Chat test:", response.content)
        return True
    except Exception as e:
        print("Chat test failed:", str(e))
        return False

def test_deepseek_embeddings():
    """Test DeepSeek embeddings"""
    try:
        embeddings = OpenAIEmbeddings(
            openai_api_key=DEEPSEEK_API_KEY,
            model="text-embedding-ada-002",
            base_url="https://api.deepseek.com/v1"
        )
        result = embeddings.embed_query("This is a test sentence.")
        print(f"Embeddings test: Generated {len(result)} dimensions")
        return True
    except Exception as e:
        print("Embeddings test failed:", str(e))
        return False

if __name__ == "__main__":
    print("Testing DeepSeek API connectivity...")
    print(f"API Key loaded: {DEEPSEEK_API_KEY is not None}")

    chat_ok = test_deepseek_chat()
    embed_ok = test_deepseek_embeddings()

    if chat_ok and embed_ok:
        print("\n✅ All DeepSeek API tests passed!")
    else:
        print("\n❌ Some tests failed. Please check your API key and network connection.")