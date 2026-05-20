from config import Config
from ui.bot import TelegramBot

def main():
    if not Config.TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not set in .env")
        return
    
    bot = TelegramBot(Config.TELEGRAM_TOKEN)
    bot.run()

if __name__ == "__main__":
    main()