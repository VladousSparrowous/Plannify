from config import Config
from ui.telegram_bot import TelegramBot

def main():
    Config.validate()
    
    bot = TelegramBot(Config.TELEGRAM_TOKEN)
    bot.run()

if __name__ == "__main__":
    main()