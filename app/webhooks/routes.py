import hmac
import hashlib
from flask import Blueprint, request, abort, current_app
from app.models import Project, ScanResult
from app import db
from app.projects.utils import run_analysis_pipeline, send_telegram_alert
from app.features import check_achievements, send_telegram_photo, generate_activity_chart

webhooks = Blueprint('webhooks', __name__)

def verify_signature(req, secret):
    """Перевіряє підпис, використовуючи конкретний секрет користувача"""
    if not secret:
        print("❌ Verify: Secret is missing")
        return False
    
    header_signature = req.headers.get('X-Hub-Signature-256')
    if not header_signature:
        print("❌ Verify: Header X-Hub-Signature-256 missing")
        return False
    
    try:
        sha_name, signature = header_signature.split('=')
    except ValueError:
        print("❌ Verify: Invalid header format")
        return False
        
    if sha_name != 'sha256':
        print("❌ Verify: Algorithm is not sha256")
        return False
    

    payload_bytes = req.get_data()
    

    mac = hmac.new(secret.strip().encode('utf-8'), payload_bytes, hashlib.sha256)
    calculated_signature = mac.hexdigest()
    


    
    return hmac.compare_digest(calculated_signature, signature)

@webhooks.route('/webhook', methods=['POST'])
def handle_webhook():


    payload = request.get_json(silent=True)
    
    if not payload:
        return 'Invalid JSON', 400

    repo_url = payload.get('repository', {}).get('clone_url')
    if not repo_url:
        return 'No repo url', 400

    print(f"🔍 Webhook for: {repo_url}")


    projects = Project.query.all()
    target_project = None
    

    search_url = repo_url.strip().lower()
    
    for p in projects:


        db_url = p.repo_url.strip().lower()
        if db_url.endswith('.git'): db_url = db_url[:-4]
        if search_url.endswith('.git'): search_url = search_url[:-4]
        
        if db_url == search_url:
            target_project = p
            break
    
    if not target_project:
        print(f"❌ Project not found for URL: {repo_url}")
        return 'Project not found', 404


    user_secret = target_project.author.webhook_secret
    if not user_secret:
        print("❌ User has no secret set")
        return 'User secret missing', 500


    if not verify_signature(request, user_secret):
        print("⛔ Signature verification FAILED")
        abort(403)

    print(f"✅ Signature verified for user: {target_project.author.username}")
    

    pusher = payload.get('pusher', {}).get('name', 'Unknown')
    message = payload.get('head_commit', {}).get('message', '')
    branch = payload.get('ref', '').split('/')[-1]
    

    results = run_analysis_pipeline(target_project.repo_url)
    
    scan = ScanResult(
        score=results['score'],
        complexity=results['complexity'],
        issues_count=results['issues'],
        details=results['log'],
        project=target_project
    )
    db.session.add(scan)
    db.session.commit()
    

    new_badges = check_achievements(target_project.author)
    

    if target_project.author.telegram_chat_id:
        send_telegram_alert(target_project.name, results, target_project.author.telegram_chat_id)

    return f'Scanned {target_project.name}', 200