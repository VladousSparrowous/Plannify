from telegram import Update
import traceback
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import logging

from connectors.jira import JiraConnector
from tools.jira_tool import JiraTool
from config import Config

# Импортируем RAG функции
from agents.Gemini_rag import rag_with_gemini, rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()

        # --- Jira tool ---
        self.jira_tool = None
        if Config.JIRA_TOKEN:
            try:
                connector = JiraConnector(
                    url=Config.JIRA_URL,
                    email=Config.JIRA_EMAIL,
                    token=Config.JIRA_TOKEN,
                    project_key=Config.JIRA_PROJECT_KEY,
                )
                self.jira_tool = JiraTool(connector)
                logger.info("✅ Jira tool initialized")
            except Exception as e:
                logger.error(f"Jira not available: {e}")

        # --- RAG инициализируется лениво через rag_pipeline ---
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("tasks", self.cmd_tasks))
        self.application.add_handler(CommandHandler("today", self.cmd_today))
        self.application.add_handler(CommandHandler("ask", self.cmd_ask))  # Новая команда для RAG
        
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Привет! Я твой ассистент.\n\n"
            "Команды:\n"
            "• /tasks — задачи Jira\n"
            "• /today — дайджест дня\n"
            "• /ask [вопрос] — ответ с RAG\n"
            "• просто напиши вопрос — отвечу через RAG\n\n"
            "Пример: /ask какие у меня задачи на сегодня?"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📌 Доступные команды:\n\n"
            "/tasks — показать мои задачи в Jira\n"
            "/today — показать дайджест на сегодня\n"
            "/ask [вопрос] — задать вопрос с поиском по истории\n\n"
            "Или просто напишите вопрос в чат."
        )

    async def cmd_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.jira_tool:
            await update.message.reply_text("❌ Jira не настроена. Проверьте переменные окружения.")
            return

        await update.message.chat.send_action(action="typing")

        user_id = str(update.effective_user.id)
        jira_user = Config.get_jira_user(user_id)
        
        if not jira_user:
            await update.message.reply_text("❌ Ваш Telegram ID не привязан к Jira пользователю.")
            return

        tasks = await self.jira_tool.get_my_tasks(jira_user)
        response = self.jira_tool.format_tasks_response(tasks)

        # Меняем parse_mode на HTML
        await update.message.reply_text(response, parse_mode="HTML")

    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Дайджест на сегодня через RAG"""
        await update.message.chat.send_action(action="typing")
        
        try:
            # Используем RAG для получения дайджеста
            response = rag_with_gemini(
                "Что у меня запланировано на сегодня? Покажи задачи, встречи и важные сообщения.",
                top_k=10
            )
            
            # Пытаемся отправить с разметкой Markdown, а если парсер упадет — отправляем как простой текст
            try:
                await update.message.reply_text(response, parse_mode="Markdown")
            except Exception as parse_err:
                logger.warning(f"Markdown parsing failed, falling back to plain text: {parse_err}")
                await update.message.reply_text(response)
                
        except Exception as e:
            # Выводим ПОЛНУЮ ошибку в консоль, чтобы вы сразу её увидели
            logger.error(f"Today command failed:\n{traceback.format_exc()}")
            await update.message.reply_text(
                "⚠️ Не удалось сформировать дайджест. Убедитесь, что:\n"
                "• Индексы данных построены (python scripts/index_data.py)\n"
                "• GEMINI_API_KEY настроен"
            )

    async def _answer_with_rag(self, update: Update, query: str):
        """Общая логика ответа через RAG"""
        await update.message.chat.send_action(action="typing")
        
        try:
            response = rag_with_gemini(query, top_k=5)
            
            # Пытаемся отправить с Markdown, при падении — отправляем как простой текст
            try:
                await update.message.reply_text(response, parse_mode="Markdown")
            except Exception as parse_err:
                logger.warning(f"Markdown parsing failed, falling back to plain text: {parse_err}")
                await update.message.reply_text(response)
                
        except Exception as e:
            # Выводим ПОЛНУЮ ошибку в консоль
            logger.error(f"RAG error:\n{traceback.format_exc()}")
            await update.message.reply_text(
                "⚠️ Ошибка при обработке запроса.\n\n"
                "Проверьте:\n"
                "1. Запущен ли скрипт индексации: python scripts/index_data.py\n"
                "2. Настроен ли GEMINI_API_KEY в .env"
            )

    async def cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /ask с RAG"""
        if not context.args:
            await update.message.reply_text("❌ Пожалуйста, укажите вопрос. Пример: /ask какие задачи в Jira?")
            return
        
        query = " ".join(context.args)
        await self._answer_with_rag(update, query)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений через RAG"""
        query = update.message.text
        await self._answer_with_rag(update, query)

    async def _answer_with_rag(self, update: Update, query: str):
        """Общая логика ответа через RAG"""
        await update.message.chat.send_action(action="typing")
        
        try:
            response = rag_with_gemini(query, top_k=5)
            await update.message.reply_text(response, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"RAG error: {e}")
            await update.message.reply_text(
                "⚠️ Ошибка при обработке запроса.\n\n"
                "Проверьте:\n"
                "1. Запущен ли скрипт индексации: python scripts/index_data.py\n"
                "2. Настроен ли GEMINI_API_KEY в .env"
            )

    def run(self):
        logger.info("🤖 Telegram bot started")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)