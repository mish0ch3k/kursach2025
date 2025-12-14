import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TG_TOKEN = os.environ.get('TG_TOKEN')
    TG_CHAT_ID = os.environ.get('TG_CHAT_ID')
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')