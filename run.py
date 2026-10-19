import os
import subprocess
import re
import time
import threading
import sys
import urllib.request
from dotenv import load_dotenv

load_dotenv()


def start_tunnel_and_run_app():
    print("Starting localhost.run tunnel...")
    tunnel_process = subprocess.Popen(
        ["ssh", "-R", "80:127.0.0.1:5000", "nokey@localhost.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    public_url = None
    for line in tunnel_process.stdout:
        print(line, end="")
        match = re.search(r'(https://[a-zA-Z0-9.-]+\.lhr\.life)', line)
        if match:
            public_url = match.group(1)
            break

    if not public_url:
        print("Error: Could not retrieve tunnel URL.")
        tunnel_process.terminate()
        tunnel_process.wait(timeout=10)
        return

    print(f"\n[AUTO-DETECTED] Tunnel is live at: {public_url}\n")

    import mail
    mail.PUBLIC_BASE_URL = public_url

    shutdown_event = threading.Event()
    mail.SHUTDOWN_EVENT = shutdown_event

    flask_thread = threading.Thread(
        target=mail.app.run,
        kwargs={"host": "127.0.0.1", "port": 5000, "debug": False, "use_reloader": False},
        daemon=True,
    )
    flask_thread.start()

    print("Flask app is running. Automatically sending approval email...")

    time.sleep(1.5)
    try:
        urllib.request.urlopen("http://127.0.0.1:5000/", timeout=10)
        print("[SUCCESS] Approval email has been sent to your inbox automatically!")
    except Exception as e:
        print(f"[WARNING] Could not auto-send email: {e}")

    print("Waiting for you to click Approve or Reject in your email...")
    shutdown_event.wait()

    print("\n[INFO] Action processed! Shutting down tunnel and server...")
    try:
        tunnel_process.terminate()
        tunnel_process.wait(timeout=10)
    except Exception:
        pass
    print("Everything closed cleanly. Goodbye!")
    sys.exit(0)

if __name__ == "__main__":
    start_tunnel_and_run_app()
