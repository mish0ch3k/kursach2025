from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Project
from app import db

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    if current_user.is_authenticated:

        user_projects = current_user.joined_projects
        return render_template('home.html', projects=user_projects)
    return render_template('landing.html')