# download_model.py
import os
from sentence_transformers import SentenceTransformer

def download_model():
    print("📥 Загрузка модели intfloat/multilingual-e5-small...")
    print("   (вес ~1GB, может занять несколько минут при первом запуске)")
    
    try:
        model = SentenceTransformer("intfloat/multilingual-e5-small")
        print("✅ Модель успешно загружена!")
        
        # Проверяем размер эмбеддинга
        test_text = "Привет, мир!"
        embedding = model.encode([test_text])
        print(f"   Размер эмбеддинга: {len(embedding[0])} измерений")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return False

if __name__ == "__main__":
    download_model()