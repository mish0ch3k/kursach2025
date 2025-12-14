import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import os


auth = Blueprint('auth', __name__)

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = generate_password_hash(password)

        new_secret = secrets.token_hex(16)
        
        user = User(username=username, email=email, password=hashed_password, webhook_secret=new_secret)
        db.session.add(user)
        db.session.commit()
        flash('Акаунт створено! Тепер ви можете увійти.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('login.html')

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'telegram_chat_id' in request.form:
            chat_id = request.form.get('telegram_chat_id')
            current_user.telegram_chat_id = chat_id
            db.session.commit()
            flash('Telegram ID збережено!', 'success')
        
        if 'regenerate_secret' in request.form:
            current_user.webhook_secret = secrets.token_hex(16)
            db.session.commit()
            flash('Новий секрет згенеровано!', 'warning')
            
        return redirect(url_for('auth.profile'))
    


    public_url = os.environ.get("FLASK_PUBLIC_URL")
    
    if public_url:

        webhook_url = f"{public_url}/webhook"
    else:

        webhook_url = url_for('webhooks.handle_webhook', _external=True)

    
    webhook_secret = current_user.webhook_secret
    
    return render_template('profile.html', webhook_url=webhook_url, webhook_secret=webhook_secret)