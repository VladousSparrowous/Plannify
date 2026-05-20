from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from connectors.jira import JiraConnector
from tools.jira_tool import JiraTool
from config import Config


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()

        # --- Jira tool (optional) ---
        self.jira_tool = None
        if getattr(Config, "JIRA_TOKEN", None):
            try:
                connector = JiraConnector(
                    url=Config.JIRA_URL,
                    email=Config.JIRA_EMAIL,
                    token=Config.JIRA_TOKEN,
                    project_key=Config.JIRA_PROJECT_KEY,
                )
                self.jira_tool = JiraTool(connector)
                print("✅ Jira tool initialized")
            except Exception as e:
                print(f"⚠️ Jira not available: {e}")

        # --- future RAG placeholders ---
        self.retriever = None
        self.digest = None

        self._setup_handlers()

    # ======================
    # HANDLERS SETUP
    # ======================
    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.cmd_start))
        self.application.add_handler(CommandHandler("help", self.cmd_help))
        self.application.add_handler(CommandHandler("tasks", self.cmd_tasks))
        self.application.add_handler(CommandHandler("today", self.cmd_today))

        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    # ======================
    # COMMANDS
    # ======================
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Привет! Я твой ассистент.\n\n"
            "Я умею:\n"
            "• /tasks — задачи Jira\n"
            "• /today — дайджест (пока MVP)\n"
            "• писать просто текстом\n\n"
            "Напиши вопрос или попробуй /tasks"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤔 Команды:\n\n"
            "/tasks — Jira задачи\n"
            "/today — дайджест дня (MVP)\n\n"
            "Или просто напиши вопрос."
        )

    async def cmd_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.jira_tool:
            await update.message.reply_text("❌ Jira не настроена")
            return

        await update.message.chat.send_action(action="typing")

        user_id = str(update.effective_user.id)
        jira_user = Config.get_jira_user(user_id)

        tasks = await self.jira_tool.get_my_tasks(jira_user)
        response = self.jira_tool.format_tasks_response(tasks)

        await update.message.reply_text(response, parse_mode="Markdown")

    async def cmd_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        MVP версия /today
        Пока без RAG — просто заглушка
        """
        await update.message.chat.send_action(action="typing")

        await update.message.reply_text(
            "📅 TODAY (MVP)\n\n"
            "Сейчас здесь будет:\n"
            "• задачи Jira\n"
            "• события Calendar\n"
            "• сообщения Telegram\n\n"
            "👉 Следующий шаг — подключение RAG pipeline"
        )

    # ======================
    # MESSAGE HANDLER
    # ======================
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_query = update.message.text.lower()

        await update.message.chat.send_action(action="typing")

        # --- simple intent for Jira ---
        if any(
            word in user_query
            for word in ["задач", "jira", "тикет", "таск"]
        ):
            if self.jira_tool:
                user_id = str(update.effective_user.id)
                jira_user = Config.get_jira_user(user_id)

                tasks = await self.jira_tool.get_my_tasks(jira_user)
                response = self.jira_tool.format_tasks_response(tasks)

                await update.message.reply_text(response, parse_mode="Markdown")
                return

        # --- fallback ---
        await update.message.reply_text(
            "Я получил твой запрос 👍\n\n"
            "Сейчас доступно:\n"
            "• /tasks — Jira\n"
            "• /today — дайджест (MVP)\n"
        )

    # ======================
    # RUN
    # ======================
    def run(self):
        print("🤖 Telegram bot started")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)