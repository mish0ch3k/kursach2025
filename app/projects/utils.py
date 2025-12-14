import os
import shutil
import subprocess
import uuid
import requests
from git import Repo
from flask import current_app

def run_command(command, cwd):
    try:
        res = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=cwd, 
            check=False,
            shell=True  
        )
        return res.stdout + res.stderr
    except Exception as e:
        return str(e)

def run_analysis_pipeline(repo_url):
    unique_folder = f"temp_scan_{uuid.uuid4().hex[:8]}"
    temp_dir = os.path.abspath(unique_folder)
    log_data = []

    try:
        log_data.append(f"[*] Cloning into {unique_folder}...")
        Repo.clone_from(repo_url, temp_dir)
        log_data.append("[+] Clone success.")

        log_data.append("[*] Running Pylint...")
        pylint_out = run_command(["pylint", "."], cwd=temp_dir)

        score = 0.0
        for line in pylint_out.split('\n'):
            if "rated at" in line:
                try:
                    parts = line.split("rated at")
                    score = float(parts[1].split("/")[0].strip())
                except: pass
        log_data.append(f"[+] Pylint Score: {score}")

        log_data.append("[*] Running Radon...")
        radon_out = run_command(["radon", "cc", ".", "-a"], cwd=temp_dir)
        complexity = 0.0
        if "Average complexity" in radon_out:
            try:
                start = radon_out.find('(') + 1
                end = radon_out.find(')')
                complexity = float(radon_out[start:end])
            except: pass
        log_data.append(f"[+] Complexity: {complexity}")

        log_data.append("[*] Running Bandit...")
        bandit_out = run_command(["bandit", "-r", ".", "-f", "json"], cwd=temp_dir)
        issues = bandit_out.count('"issue_text":')
        log_data.append(f"[+] Security Issues: {issues}")

        full_log = "\n".join(log_data) + "\n\n=== DETAILS ===\n" + pylint_out[-500:]

        return {
            'score': score,
            'complexity': complexity,
            'issues': issues,
            'log': full_log
        }

    except Exception as e:
        return {'score': 0, 'complexity': 0, 'issues': 0, 'log': str(e)}

    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except: pass

def send_telegram_alert(project_name, results, chat_id):
    token = current_app.config.get('TG_TOKEN')
    
    if not token or not chat_id:
        print("Telegram token or Chat ID missing.")
        return

    text = (
        f"🚀 **Перевірку завершено!**\n"
        f"Проект: {project_name}\n"
        f"-------------------\n"
        f"🏆 Оцінка: {results['score']}/10\n"
        f"🧩 Складність: {results['complexity']}\n"
        f"🛡 Вразливості: {results['issues']}\n"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegram Error: {e}")