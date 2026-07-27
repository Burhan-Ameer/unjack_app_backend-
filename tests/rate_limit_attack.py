import json
import urllib.request
import urllib.error

URL = "http://localhost:8000/api/v1/auth/login"

def run_attack():
    print("=== Simulating Rate Limiting Attack (16 login attempts) ===")
    
    payload = {
        "email": "hacker@test.com",
        "password": "wrong_password_attempt"
    }
    req_data = json.dumps(payload).encode("utf-8")
    
    for i in range(1, 17):
        req = urllib.request.Request(
            URL, 
            data=req_data, 
            method="POST", 
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                status = response.status
                print(f"Request #{i}: Status {status}")
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                message = body.get("error", {}).get("message", e.reason)
            except Exception:
                message = e.reason
            print(f"Request #{i}: Status {status} | Error: {message}")
            
            if status == 429:
                print(f"\n🔥 SUCCESS: Rate limiter blocked the attack on request #{i}!")
                print("Check your database logs: SELECT * FROM db_logs;")
                return
        except Exception as e:
            print(f"Request #{i}: Failed to connect to server: {e}")
            return
            
    print("\n❌ FAILED: Made all 16 requests without being blocked.")
    print("Did you restart the backend container after changing the settings?")

if __name__ == "__main__":
    run_attack()
