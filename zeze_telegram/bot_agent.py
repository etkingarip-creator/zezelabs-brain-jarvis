# -*- coding: utf-8 -*-
import os
import sys
import json
import asyncio
import threading
from telegram import Update  # pyrefly: ignore[missing-import]
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes  # pyrefly: ignore[missing-import]

# Proje köküne path ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.mq_client import MQClient
from core.memory.db_client import TieredMemoryClient

# Config — token .env'den okunur, asla hardcode edilmez
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
REDIS_CHAT_ID_KEY = "config:admin_chat_id"


class TelegramGateway:
    def __init__(self):
        print("[TelegramGateway] Baslatiliyor...")
        self.mq = MQClient()
        self.memory = TieredMemoryClient()
        self.app = ApplicationBuilder().token(BOT_TOKEN).build()
        self.loop = asyncio.get_event_loop()

        self.admin_chat_id = None
        if self.memory._redis:
            try:
                saved_id = self.memory._redis.get(REDIS_CHAT_ID_KEY)
                if saved_id:
                    self.admin_chat_id = int(saved_id)
                    print(f"[TelegramGateway] Redis'ten Chat ID yuklendi: {self.admin_chat_id}")
            except Exception as e:
                print(f"[TelegramGateway] Redis Chat ID okuma hatasi: {e}")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.admin_chat_id = update.effective_chat.id
        if self.memory._redis:
            try:
                self.memory._redis.set(REDIS_CHAT_ID_KEY, str(self.admin_chat_id))
                print(f"[TelegramGateway] Chat ID Redis'e kaydedildi: {self.admin_chat_id}")
            except Exception as e:
                print(f"[TelegramGateway] Redis kaydetme hatasi: {e}")

        await update.message.reply_text(
            "\U0001f3db **Zezelabs Komuta Merkezi Aktif!**\n"
            f"Chat ID: `{self.admin_chat_id}`\n\n"
            "Su andan itibaren:\n"
            "1. Raporlar buraya gelecek.\n"
            "2. Hafiza guncellemeleri buraya gelecek.\n"
            "3. Yazdigin her sey Jarvis'e iletilecek.",
            parse_mode="Markdown"
        )

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sistem durumunu kontrol eder ve raporlar."""
        lines = ["\U0001f7e2 *ZOM Sistem Durumu*\n"]

        # Redis
        if self.memory._redis:
            try:
                self.memory._redis.ping()
                lines.append("\u2705 Redis: Aktif")
            except Exception:
                lines.append("\u274c Redis: Baglanti Hatasi")
        else:
            lines.append("\u274c Redis: Kullanilamiyor")

        # ChromaDB
        if self.memory._collection:
            lines.append("\u2705 ChromaDB: Aktif")
        else:
            lines.append("\u274c ChromaDB: Kullanilamiyor")

        lines.append("\n\U0001f310 Jarvis Bridge ve RabbitMQ baglantilari asenkron calisiyor.")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gelen mesajlari ZOM orkestratörüne iletir."""
        user_msg = update.message.text
        print(f"[TelegramGateway] Gelen mesaj: {user_msg}")

        task_payload = {
            "task": user_msg,
            "source": f"Telegram:{update.effective_user.id}",
            "type": "telegram_command"
        }

        self.mq.publish("main_orchestrator_queue", task_payload)
        await update.message.reply_text("\U0001f680 Komut orkestratöre iletildi.")

    def mq_callback(self, ch, method, properties, body):
        """RabbitMQ'dan gelen raporlari Telegram'a gönderir."""
        try:
            data = json.loads(body)
            msg_type = data.get("type", "notification")
            task_desc = data.get("task", "Isimsiz gorev")

            if msg_type == "memory_update":
                text = f"\U0001f9e0 *[ZEZEPEDIA] Yeni Hafiza Kaydi*\n\n{task_desc}"
            elif msg_type == "report":
                text = f"\U0001f4ca *[RAPOR] Gorev Tamamlandi*\n\n{task_desc}"
            else:
                text = f"\U0001f514 *[BILDIRIM]*\n{task_desc}"

            if self.admin_chat_id:
                asyncio.run_coroutine_threadsafe(
                    self.app.bot.send_message(
                        chat_id=self.admin_chat_id,
                        text=text,
                        parse_mode="Markdown"
                    ),
                    self.loop
                )
        except Exception as e:
            print(f"[TelegramGateway] MQ isleme hatasi: {e}")

    def run_mq_listener(self):
        """RabbitMQ'yu ayri bir thread'de dinler."""
        self.mq.connect()
        self.mq.declare_queue("telegram_out_queue")
        self.mq.consume("telegram_out_queue", self.mq_callback)

    def start(self):
        mq_thread = threading.Thread(target=self.run_mq_listener, daemon=True)
        mq_thread.start()
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        print("[TelegramGateway] Bot dinlemede...")
        self.app.run_polling()


if __name__ == "__main__":
    gateway = TelegramGateway()
    gateway.start()
