from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = input("Введіть Email користувача, якого зробити Адміном: ")
    user = User.query.filter_by(email=email).first()
    
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"✅ Успіх! Користувач {user.username} тепер Адміністратор.")
    else:
        print("❌ Користувача з таким email не знайдено.")