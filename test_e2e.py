import pytest
from playwright.sync_api import Page, BrowserContext, expect
import requests
import hmac
import hashlib
import json
import random
import time
import sqlite3



RunID = random.randint(10000, 99999)

BASE_URL = "http://127.0.0.1:5000"
REPO_URL = f"https://github.com/test/repo_{RunID}.git" # Унікальний URL
WEBHOOK_ENDPOINT = f"{BASE_URL}/webhook"

OWNER_USER = f"Owner_{RunID}"
OWNER_EMAIL = f"owner_{RunID}@test.com"
COLLAB_USER = f"Collab_{RunID}"
COLLAB_EMAIL = f"collab_{RunID}@test.com"
PASSWORD = "Password123!"
PROJECT_NAME = f"Mega Project {RunID}"



def sign_request(secret: str, data: bytes) -> str:
    """Генерує X-Hub-Signature-256 для емуляції GitHub"""
    hash_object = hmac.new(secret.encode('utf-8'), data, hashlib.sha256)
    return f"sha256={hash_object.hexdigest()}"

def register_and_login(page: Page, username, email, password):

    page.goto(f"{BASE_URL}/register")
    page.fill('input[name="username"]', username)
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    expect(page.locator(".alert-success")).to_be_visible()


    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    expect(page.locator("h2")).to_contain_text("Мої проекти")

def make_user_admin(email):
    """Пряме втручання в БД для надання прав адміна"""
    print(f"[*] [DB] Надаємо права адміністратора для {email}...")
    try:


        
        conn = sqlite3.connect('instance/site.db')
        c = conn.cursor()
        c.execute("UPDATE user SET is_admin = 1 WHERE email = ?", (email,))
        conn.commit()
        changes = c.rowcount
        conn.close()
        
        if changes == 0:
            print(f"⚠️ Warning: User {email} not found in DB at {db_path}!")
        else:
            print(f"    -> [DB] Success! User {email} is now ADMIN.")
        
    except Exception as e:
        print(f"    -> [DB Error] Failed to promote user: {e}")
        raise e



def test_full_lifecycle(browser):

    context_owner = browser.new_context()
    context_collab = browser.new_context()
    

    context_owner.tracing.start(screenshots=True, snapshots=True)
    context_collab.tracing.start(screenshots=True, snapshots=True)
    
    try:
        page_owner = context_owner.new_page()
        page_collab = context_collab.new_page()




        print(f"\n[*] [Owner] Реєстрація: {OWNER_USER}")
        register_and_login(page_owner, OWNER_USER, OWNER_EMAIL, PASSWORD)

        print("[*] [Owner] Отримання Webhook Secret...")
        page_owner.click("text=⚙️ Налаштування")
        
        secret_input = page_owner.locator("#secretInput")
        expect(secret_input).to_be_visible()
        webhook_secret = secret_input.input_value()
        assert len(webhook_secret) > 0
        print(f"    -> Secret found: {webhook_secret[:5]}...")




        print("[*] [Owner] Створення проекту...")
        page_owner.click("text=Новий проект")
        page_owner.fill('input[name="name"]', PROJECT_NAME)
        page_owner.fill('input[name="url"]', REPO_URL)
        page_owner.click('button:has-text("Створити")')
        
        expect(page_owner.locator("body")).to_contain_text(PROJECT_NAME)
        expect(page_owner.locator(".badge:has-text('Admin')")).to_be_visible()




        print("[*] [Owner] Отримання коду запрошення...")
        page_owner.click(f".card:has-text('{PROJECT_NAME}') >> text=Дашборд")
        
        invite_code = None
        def handle_dialog(dialog):
            nonlocal invite_code
            msg = dialog.message
            invite_code = msg.split(": ")[1].strip()
            print(f"    -> Code intercepted: {invite_code}")
            dialog.accept()

        page_owner.on("dialog", handle_dialog)
        page_owner.locator(".fa-plus").click() 
        
        page_owner.wait_for_timeout(1000)
        assert invite_code is not None
        

        page_owner.remove_listener("dialog", handle_dialog)




        print(f"[*] [Collab] Реєстрація другого юзера: {COLLAB_USER}")
        register_and_login(page_collab, COLLAB_USER, COLLAB_EMAIL, PASSWORD)

        print("[*] [Collab] Приєднання до проекту...")
        page_collab.click("text=Приєднатися")
        page_collab.fill('input[name="invite_code"]', invite_code)
        page_collab.click('button:has-text("Приєднатися")')

        expect(page_collab.locator(".alert-success")).to_contain_text(f'Успішно приєднано до "{PROJECT_NAME}"')




        print("[*] [System] Надсилаємо фейковий GitHub Push...")
        
        webhook_payload = {
            "ref": "refs/heads/main",
            "repository": {"clone_url": REPO_URL, "name": "requests"},
            "pusher": {"name": "GitHub_Bot"},
            "head_commit": {"message": "E2E Automated Fix"}
        }
        
        payload_bytes = json.dumps(webhook_payload).encode('utf-8')
        signature = sign_request(webhook_secret, payload_bytes)
        
        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
            "User-Agent": "GitHub-Hookshot/123"
        }

        response = requests.post(WEBHOOK_ENDPOINT, data=payload_bytes, headers=headers)
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        print("    -> Webhook accepted.")




        print("[*] [Owner] Перевірка результатів...")
        page_owner.reload()
        expect(page_owner.locator("table tbody tr")).to_be_visible()
        expect(page_owner.locator("#qualityChart")).to_be_visible()




        print("[*] [Owner] Перевірка PDF...")
        with page_owner.expect_popup() as popup_info:
            page_owner.click("text=Звіт PDF")
        
        page_pdf = popup_info.value
        page_pdf.wait_for_load_state()
        assert "/pdf" in page_pdf.url
        print("    -> PDF opened.")
        page_pdf.close()




        print("[*] [Owner] Тестування Адмінки...")


        page_owner.goto(f"{BASE_URL}/admin/users")
        expect(page_owner.locator("body")).to_contain_text("У вас немає прав")
        

        make_user_admin(OWNER_EMAIL)


        page_owner.goto(f"{BASE_URL}/admin")
        expect(page_owner.locator(".navbar-brand")).to_contain_text("QualitySystem Admin")


        page_owner.click("text=Користувачі")
        print(f"    -> Searching for {OWNER_EMAIL}...")
        page_owner.locator('input[name="search"]').fill(OWNER_EMAIL)
        page_owner.locator('input[name="search"]').press("Enter")
        expect(page_owner.locator(f"td:has-text('{OWNER_EMAIL}')")).to_be_visible()
        
        page_owner.goto(f"{BASE_URL}/home")




        print("[*] [Collab] Вихід з проекту...")
        page_collab.goto(f"{BASE_URL}/home")
        
        collab_card = page_collab.locator(f".card:has-text('{PROJECT_NAME}')")
        expect(collab_card).to_be_visible()
        collab_card.locator("[data-bs-toggle='dropdown']").click()

        page_collab.on("dialog", lambda d: d.accept())
        page_collab.click("text=Покинути")
        expect(page_collab.locator(f".card:has-text('{PROJECT_NAME}')")).not_to_be_visible()

        print("[*] [Owner] Видалення проекту...")
        page_owner.goto(f"{BASE_URL}/home")
        
        owner_card = page_owner.locator(f".card:has-text('{PROJECT_NAME}')")
        expect(owner_card).to_be_visible()
        owner_card.locator("[data-bs-toggle='dropdown']").click()

        page_owner.on("dialog", lambda d: d.accept())
        page_owner.click("text=Видалити проект")
        expect(page_owner.locator(".alert-success")).to_contain_text("видалено")

        print("\n✅ E2E TEST PASSED SUCCESSFULLY!")

    except Exception as e:
        context_owner.tracing.stop(path="trace_owner.zip")
        context_collab.tracing.stop(path="trace_collab.zip")
        raise e
    
    finally:
        context_owner.close()
        context_collab.close()