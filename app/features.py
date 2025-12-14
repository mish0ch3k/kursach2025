import matplotlib
matplotlib.use('Agg') # Важливо для роботи на сервері без екрану
import matplotlib.pyplot as plt
import io
import datetime
from app import db
from app.models import User, ScanResult, Project
import requests
import os


def check_achievements(user):
    new_badges = []
    now = datetime.datetime.now()
    

    if 0 <= now.hour <= 24:
        if user.add_achievement("🦉 Нічна сова"):
            new_badges.append("🦉 Нічна сова")



    scan_count = ScanResult.query.join(Project).filter(Project.author == user).count()
    if scan_count >= 1:
        if user.add_achievement("⛏ Стахановець"):
            new_badges.append("⛏ Стахановець")

    db.session.commit()
    return new_badges

def get_weekly_leaderboard():

    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    


    leaderboard = db.session.query(User.username, db.func.count(ScanResult.id))\
        .join(Project, Project.user_id == User.id)\
        .join(ScanResult, ScanResult.project_id == Project.id)\
        .filter(ScanResult.timestamp >= one_week_ago)\
        .group_by(User.id)\
        .order_by(db.func.count(ScanResult.id).desc())\
        .limit(3).all()
        
    text = "🏆 **Топ контриб'юторів тижня:**\n"
    for idx, (name, count) in enumerate(leaderboard, 1):
        text += f"{idx}. {name} — {count} дій\n"
    return text


def generate_activity_chart(project_id):

    scans = ScanResult.query.filter_by(project_id=project_id).order_by(ScanResult.timestamp).all()
    if not scans:
        return None

    dates = [s.timestamp.strftime('%m-%d') for s in scans]
    scores = [s.score for s in scans]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, scores, marker='o', linestyle='-', color='b')
    plt.title('Активність проекту (Score)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()


    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf


def generate_ai_summary(reports_text):
    """
    Тут має бути запит до OpenAI/Claude.
    Оскільки API платні, це приклад структури.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "⚠️ AI не налаштовано (відсутній API KEY)."

    prompt = f"Проаналізуй звіти розробників і напиши смішний підсумок хто що робив:\n{reports_text}"
    



    
    return "🤖 (AI Імітація): Іван фіксив баги, Марія писала код, а сервер відпочивав."


def send_telegram_photo(chat_id, photo_buffer, caption=""):
    token = os.environ.get('TG_TOKEN')
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    files = {'photo': photo_buffer}
    data = {'chat_id': chat_id, 'caption': caption}
    try:
        requests.post(url, data=data, files=files)
    except Exception as e:
        print(f"TG Error: {e}")