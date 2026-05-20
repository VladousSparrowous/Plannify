#!/usr/bin/env python
"""Тест доступности Gemini модели"""

from config import Config
from google import genai
from google.genai import types

def test_gemini_connection():
    """Проверяет подключение к Gemini API и доступность модели"""
    
    print("="*50)
    print("🔍 Testing Gemini API Connection")
    print("="*50)
    
    # 1. Проверяем API ключ
    if not Config.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in .env")
        print("   Please add: GEMINI_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found: {Config.GEMINI_API_KEY[:10]}...")
    
    # 2. Пробуем подключиться
    try:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
        print("✅ Gemini client created")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False
    
    # 3. Проверяем доступные модели
    try:
        print("\n📋 Available models:")
        models = client.models.list()
        gemini_models = []
        
        for model in models:
            if 'gemini' in model.name.lower():
                gemini_models.append(model.name)
                print(f"   - {model.name}")
        
        if not gemini_models:
            print("   No Gemini models found!")
            return False
            
    except Exception as e:
        print(f"❌ Failed to list models: {e}")
        return False
    
    # 4. Тестируем конкретную модель
    MODEL_NAME = "gemini-2.5-flash-lite"
    
    print(f"\n🔬 Testing model: {MODEL_NAME}")
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="Say 'OK' if you can read this",
            config=types.GenerateContentConfig(
                max_output_tokens=10
            )
        )
        
        print(f"✅ Model responded: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        
        # Пробуем альтернативные модели
        print("\n🔄 Trying alternative models...")
        
        alternatives = [
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-pro",
            "gemini-2.0-flash-exp"
        ]
        
        for alt_model in alternatives:
            try:
                response = client.models.generate_content(
                    model=alt_model,
                    contents="Say OK",
                    config=types.GenerateContentConfig(max_output_tokens=5)
                )
                print(f"   ✅ {alt_model} works!")
                print(f"   Use this model instead of gemini-2.5-flash-lite")
                return True
            except:
                print(f"   ❌ {alt_model} failed")
        
        return False

def test_rag_without_gemini():
    """Тестирует RAG пайплайн без вызова Gemini"""
    
    print("\n" + "="*50)
    print("🔍 Testing RAG Pipeline (without Gemini)")
    print("="*50)
    
    try:
        from agents.Gemini_rag import rag_pipeline
        
        query = "тестовый запрос"
        result = rag_pipeline(query, top_k=3, verbose=True)
        
        print(f"\n✅ RAG pipeline works!")
        print(f"   Context length: {len(result['context'])} chars")
        print(f"   Results count: {len(result['results'])}")
        
        if result['context']:
            print("\n📚 Sample context:")
            print("-"*30)
            print(result['context'][:300])
            print("-"*30)
        
        return True
        
    except ImportError as e:
        print(f"❌ RAG pipeline import error: {e}")
        return False
    except Exception as e:
        print(f"❌ RAG pipeline error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Gemini Model Test Suite")
    print("="*50 + "\n")
    
    # Тест 1: Подключение к Gemini
    gemini_ok = test_gemini_connection()
    
    # Тест 2: RAG пайплайн
    rag_ok = test_rag_without_gemini()
    
    # Итоги
    print("\n" + "="*50)
    print("📊 RESULTS:")
    print("="*50)
    print(f"Gemini API: {'✅ OK' if gemini_ok else '❌ FAILED'}")
    print(f"RAG Pipeline: {'✅ OK' if rag_ok else '❌ FAILED'}")
    
    if not gemini_ok:
        print("\n💡 TROUBLESHOOTING:")
        print("   1. Check your API key: https://aistudio.google.com/app/apikey")
        print("   2. Enable billing if required")
        print("   3. Check internet connection")
        print("   4. Try different model name")
    
    print("="*50)