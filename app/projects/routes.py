import uuid
from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import Project, ScanResult
from app.projects.utils import run_analysis_pipeline, send_telegram_alert

projects = Blueprint('projects', __name__)

@projects.route("/project/new", methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        name = request.form.get('name')
        url = request.form.get('url').strip()

        if not url.endswith('.git'):
            url += '.git'


        inv_code = str(uuid.uuid4())[:8]

        project = Project(name=name, repo_url=url, author=current_user, invite_code=inv_code)
        

        project.members.append(current_user)
        
        db.session.add(project)
        db.session.commit()
        flash(f'Проект створено! Ваш код запрошення: {inv_code}', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_project.html')


@projects.route("/project/join", methods=['GET', 'POST'])
@login_required
def join_project():
    if request.method == 'POST':
        code = request.form.get('invite_code').strip()
        project = Project.query.filter_by(invite_code=code).first()
        
        if project:
            if current_user in project.members:
                flash('Ви вже є учасником цього проекту.', 'info')
            else:
                project.members.append(current_user)
                db.session.commit()
                flash(f'Успішно приєднано до "{project.name}"!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Невірний код запрошення.', 'danger')
            
    return render_template('join_project.html')


@projects.route("/project/<int:project_id>/delete", methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    

    if project.author == current_user:

        ScanResult.query.filter_by(project_id=project.id).delete()

        db.session.delete(project)
        db.session.commit()
        flash('Проект та всі дані видалено!', 'success')
    

    elif current_user in project.members:
        project.members.remove(current_user)
        db.session.commit()
        flash('Ви покинули проект.', 'info')
    
    else:
        flash('У вас немає прав для цієї дії.', 'danger')

    return redirect(url_for('main.home'))


@projects.route("/project/<int:project_id>")
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    

    if current_user not in project.members:
         flash('У вас немає доступу до цього проекту', 'danger')
         return redirect(url_for('main.home'))

    scans = ScanResult.query.filter_by(project_id=project.id).order_by(ScanResult.timestamp.desc()).all()
    labels = [scan.timestamp.strftime('%H:%M') for scan in scans[:10][::-1]]
    data = [scan.score for scan in scans[:10][::-1]]
    
    return render_template('project_detail.html', project=project, scans=scans, labels=labels, data=data)

@projects.route("/project/<int:project_id>/scan")
@login_required
def run_scan(project_id):
    project = Project.query.get_or_404(project_id)
    
    results = run_analysis_pipeline(project.repo_url)
    
    scan = ScanResult(
        score=results['score'],
        complexity=results['complexity'],
        issues_count=results['issues'],
        
        test_coverage=results['coverage'],
        status=results['status'],
        
        details=results['log'],
        project=project
    )
    db.session.add(scan)
    db.session.commit()
    
    send_telegram_alert(project.name, results)
    
    if results['status'] == 'Pass':
        flash('Сканування успішне! Проект пройшов перевірку.', 'success')
    else:
        flash('Сканування завершено. Виявлено критичні помилки!', 'danger')
        
    return redirect(url_for('projects.project_detail', project_id=project.id))

@projects.route("/project/<int:project_id>/pdf")
@login_required
def export_pdf(project_id):
    project = Project.query.get_or_404(project_id)
    scans = ScanResult.query.filter_by(project_id=project.id).all()
    rendered = render_template('pdf_report.html', project=project, scans=scans)

    return rendered 
