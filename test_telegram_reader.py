import asyncio
from config import Config
from connectors.telegram_reader import TelegramReaderConnector

async def test_telegram_reader():
    Config.validate()
    
    if not Config.TELEGRAM_TOKEN:
        print("❌ Telegram токен не настроен")
        return
    
    reader = TelegramReaderConnector(
        token=Config.TELEGRAM_TOKEN
    )
    
    # Проверяем подключение
    if not await reader.validate():
        print("❌ Ошибка подключения к Telegram")
        return
    
    # Получаем список чатов для чтения
    chat_ids = Config.get_chat_list()
    if not chat_ids:
        print("⚠️ Не указаны чаты для чтения (TELEGRAM_CHATS_TO_READ в .env)")
        print("   Как получить ID чата:")
        print("   1. Добавьте @userinfobot в чат")
        print("   2. Отправьте любое сообщение")
        print("   3. Бот ответит с ID чата")
        return
    
    print(f"\n📨 Читаем сообщения из {len(chat_ids)} чатов...")
    
    for chat_id in chat_ids:
        print(f"\n--- Чат {chat_id} ---")
        messages = await reader.get_chat_messages(chat_id, limit=5)
        
        if messages:
            for msg in messages:
                print(f"  • {msg['text'][:50] if msg['text'] else '[без текста]'}")
                print(f"    🔗 {msg['link']}")
        else:
            print("  Нет сообщений")
    
    # Тест поиска
    if messages:
        test_query = messages[0]['text'][:30]  # первый текст как запрос
        print(f"\n🔍 Поиск: '{test_query}'")
        results = await reader.search_in_chat(chat_ids[0], test_query, limit=3)
        print(f"  Найдено: {len(results)} сообщений")

def main():
    asyncio.run(test_telegram_reader())

if __name__ == "__main__":
    main()