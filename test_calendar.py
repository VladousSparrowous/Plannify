from config import Config
from connectors.google_calendar import GoogleCalendarConnector

def test_calendar():
    Config.validate()
    
    if not Config.GOOGLE_CREDENTIALS_PATH:
        print("❌ Google Calendar не настроен. Добавьте GOOGLE_CREDENTIALS_PATH в .env")
        return
    
    try:
        connector = GoogleCalendarConnector(
            credentials_path=Config.GOOGLE_CREDENTIALS_PATH,
            token_path=Config.GOOGLE_TOKEN_PATH
        )
        
        if connector.validate():
            print("\n📅 События на сегодня:")
            events = connector.get_today_events()
            
            if events:
                for event in events:
                    meta = event['metadata']
                    print(f"  • {event['title']}")
                    if meta['is_all_day']:
                        print(f"    Весь день")
                    else:
                        print(f"    {meta['start_human']} — {meta['end_human']}")
            else:
                print("  Нет событий на сегодня")
        else:
            print("❌ Ошибка подключения к Google Calendar")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Убедитесь, что:")
        print("  1. Файл credentials.json существует в корне проекта")
        print("  2. Включен Google Calendar API в консоли")
        print("  3. Вы скачали правильные credentials")

if __name__ == "__main__":
    test_calendar()