from app import scheduler, db
from app.models import User
from app.projects.utils import send_telegram_alert
import requests
import os
import random


@scheduler.task('cron', id='daily_meeting', hour=10, minute=0)
def daily_meeting_ping():
    with scheduler.app.app_context():
        users = User.query.filter(User.telegram_chat_id != None).all()
        
        for user in users:
            msg = "👋 **Дейлі мітинг!**\nЧас писати звіти! Що ви робили вчора?"
            send_text(user.telegram_chat_id, msg)

def send_text(chat_id, text):
    token = os.environ.get('TG_TOKEN')
    if not token: return
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                  json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})