import secrets
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
import json
import hashlib

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    is_admin = db.Column(db.Boolean, default=False)
    achievements_json = db.Column(db.Text, default='[]')
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    telegram_chat_id = db.Column(db.String(50), nullable=True)
    webhook_secret = db.Column(db.String(32), default=lambda: secrets.token_hex(16))
    

    projects_created = db.relationship('Project', backref='author', lazy=True)
    

    joined_projects = db.relationship('Project', secondary=project_members, back_populates='members')
    def get_achievements(self):
        try:
            return json.loads(self.achievements_json)
        except:
            return []

    def add_achievement(self, title):
        current = self.get_achievements()
        if title not in current:
            current.append(title)
            self.achievements_json = json.dumps(current)
            return True # Повернути True, якщо це нова ачівка
        return False
    
    def avatar(self, size):

        digest = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
class Project(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    repo_url = db.Column(db.String(200), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    

    invite_code = db.Column(db.String(10), unique=True, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scans = db.relationship('ScanResult', backref='project', lazy=True)
    

    members = db.relationship('User', secondary=project_members, back_populates='joined_projects')


class ScanResult(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float)
    complexity = db.Column(db.Float)
    issues_count = db.Column(db.Integer)
    details = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)