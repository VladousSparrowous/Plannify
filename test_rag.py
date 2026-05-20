# test_rag.py
from storage.vector_store import VectorStore

def test_vector_store():
    print("🧪 Тестирование Vector Store с multilingual-e5-small")
    print("=" * 50)
    
    # Создаём хранилище
    store = VectorStore(persist_dir="./data/test_chroma")
    
    # Тестовые сообщения на русском
    test_messages = [
        {
            'source': 'telegram',
            'source_id': 'msg_1',
            'text': 'Нужно срочно починить авторизацию на сайте, пользователи не могут войти',
            'timestamp': '2024-01-15T10:00:00',
            'link': 'https://t.me/c/123/1',
            'metadata': {'chat_title': 'Dev Chat', 'sender': 'ivan'}
        },
        {
            'source': 'telegram',
            'source_id': 'msg_2',
            'text': 'Встреча по планированию спринта завтра в 11:00',
            'timestamp': '2024-01-15T11:00:00',
            'link': 'https://t.me/c/123/2',
            'metadata': {'chat_title': 'Project Chat', 'sender': 'petr'}
        },
        {
            'source': 'telegram',
            'source_id': 'msg_3',
            'text': 'Баг: приложение падает на iOS после обновления',
            'timestamp': '2024-01-15T12:00:00',
            'link': 'https://t.me/c/123/3',
            'metadata': {'chat_title': 'QA Chat', 'sender': 'olga'}
        },
    ]
    
    # Добавляем сообщения
    print("\n📝 Добавление сообщений...")
    added = store.add_messages_batch(test_messages)
    print(f"  Добавлено: {added} сообщений")
    print(f"  Всего в хранилище: {store.count_messages()}")
    
    # Тест поиска на русском
    print("\n🔍 Поиск по запросу: 'авторизация'")
    results = store.search_messages("авторизация", limit=2)
    for r in results:
        print(f"  • {r['text'][:60]}...")
        print(f"    Расстояние: {r['distance']:.4f}")
    
    print("\n🔍 Поиск по запросу: 'встреча'")
    results = store.search_messages("встреча", limit=2)
    for r in results:
        print(f"  • {r['text'][:60]}...")
    
    print("\n🔍 Поиск по запросу: 'iOS'")
    results = store.search_messages("iOS", limit=2)
    for r in results:
        print(f"  • {r['text'][:60]}...")
    
    print("\n✅ Тест пройден!")

if __name__ == "__main__":
    test_vector_store()