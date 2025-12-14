from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_admin import Admin # Імпортуємо клас Admin
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
scheduler = APScheduler()



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    

    if not app.config.get('TESTING') and not scheduler.running:
        scheduler.init_app(app)
        scheduler.start()
    


    admin = Admin(app, name='QualitySystem Admin') # Передаємо app одразу в конструктор


    from app.models import User, Project, ScanResult
    from app.admin_views import UserView, ProjectView, SecureModelView
    


    admin.add_view(UserView(User, db.session, name='Користувачі', endpoint='admin_users', url='users'))
    admin.add_view(ProjectView(Project, db.session, name='Проекти', endpoint='admin_projects', url='projects'))
    admin.add_view(SecureModelView(ScanResult, db.session, name='Звіти', endpoint='admin_reports', url='reports'))


    from app.users.routes import auth
    from app.main.routes import main
    from app.projects.routes import projects
    from app.webhooks.routes import webhooks

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(projects)
    app.register_blueprint(webhooks)
    
    if not app.config.get('TESTING'):
        from app import tasks

    return app