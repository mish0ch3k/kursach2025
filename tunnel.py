from pyngrok import ngrok
import time

public_url = ngrok.connect(5000).public_url
print(f"Ngrok URL: {public_url}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped")