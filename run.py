import os
import sys
from app import create_app, db


try:
    from pyngrok import ngrok
except ImportError:
    ngrok = None

app = create_app()

def start_ngrok():

    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        try:

            public_url = ngrok.connect(5000).public_url
            print(f"\n * Ngrok Tunnel: {public_url}")
            

            os.environ["FLASK_PUBLIC_URL"] = public_url
        except Exception as e:
            print(f"Ngrok error: {e}")

if __name__ == '__main__':

    if ngrok:
        start_ngrok()
        
    with app.app_context():
        db.create_all()
        

    app.run(debug=True)