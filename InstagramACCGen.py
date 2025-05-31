import requests
import uuid
import time
import random
import hashlib
import urllib.parse
import json
from datetime import datetime
from faker import Faker
import re

BLOCK_VERSION = 'a399f367a2e4aa3e40cdb4aab6535045b23db15f3dea789880aa0970463de062'
APP_ID = '567067343352427'
SIGNATURE = "46024e8f31e295869a0e861eaed42cb1dd8454b55232d85f6c6764365079374b"
PASSWORD = "asdasd123!"

faker = Faker()

proxies_list = [
    "http://user:pass@host:port",
]

def get_proxy():
    proxy = random.choice(proxies_list)
    return {
        "http": proxy,
        "https": proxy
    }

def generate_uuid(prefix='', suffix=''):
    return f"{prefix}{uuid.uuid4()}{suffix}"

def generate_android_device_id():
    return f"android-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}"

def generate_user_agent():
    try:
        with open("ua.txt", "r") as f:
            agents = f.read().splitlines()
        user = random.choice(agents).split(",")
        return f'Instagram 261.0.0.21.111 Android ({user[7]}/{user[6]}; {user[5]}dpi; {user[4]}; {user[0]}; {user[1]}; {user[2]}; {user[3]}; en_US; {user[9]})'
    except FileNotFoundError:
        raise Exception("User-Agent file 'ua.txt' not found!")

def get_mid():
    try:
        response = requests.get("https://i.instagram.com/api/v1/accounts/login", proxies=get_proxy(), timeout=10)
        return response.cookies.get("mid") or f'Y4nS4g{"".join(random.choices("QWERTYUIOPASDFGHJKLZXCVBNM", k=8))}zwIrWdeYLcD9Shxj'
    except Exception:
        return f'Y4nS4g{"".join(random.choices("QWERTYUIOPASDFGHJKLZXCVBNM", k=8))}zwIrWdeYLcD9Shxj'

def generate_jazoest(symbols: str) -> str:
    return f"2{sum(ord(s) for s in symbols)}"

def generate_username():
    return faker.user_name() + str(random.randint(1000, 9999))

def get_emails():
    name = faker.user_name() + "asd12"
    email = name + "@dcpa.net"
    password = "asdasd123!"
    url = 'https://api.mail.tm/accounts'
    data = {'address': email, 'password': password}
    try:
        req = requests.post(url, json=data, proxies=get_proxy(), timeout=15)
        if req.status_code == 201:
            token_url = 'https://api.mail.tm/token'
            req2 = requests.post(token_url, json=data, proxies=get_proxy(), timeout=15)
            token_data = req2.json()
            return email, token_data.get("token")
    except Exception as e:
        print(f"[!] get_emails error: {e}")
    return None, None

def get_verification_code(token, wait_time=60, check_interval=5):
    url = 'https://api.mail.tm/messages'
    headers = {'Authorization': f'Bearer {token}'}
    start_time = time.time()

    while time.time() - start_time < wait_time:
        try:
            req = requests.get(url, headers=headers, proxies=get_proxy(), timeout=15)
            if req.status_code == 200:
                data = req.json()
                if data.get('hydra:totalItems', 0) > 0:
                    subject = data['hydra:member'][0]['subject']
                    match = re.search(r'(\d{6})\s+is your Instagram code', subject)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"[!] get_verification_code error: {e}")
        print("[...] Waiting for verification code...")
        time.sleep(check_interval)

    print("[×] Verification code did not arrive in time.")
    return None

def create_account(email, token):
    if not email or not token:
        print("[×] Email or token generation failed.")
        return

    device_id = generate_uuid()
    family_id = generate_uuid()
    android_id = generate_android_device_id()
    user_agent = generate_user_agent()
    x_mid = get_mid()
    adid = str(uuid.uuid4())
    waterfall_id = str(uuid.uuid4())
    username = generate_username()
    jazoest = generate_jazoest(family_id)

    headers = {
        'Host': 'i.instagram.com',
        'User-Agent': user_agent,
        'X-Ig-Device-Id': device_id,
        'X-Ig-Family-Device-Id': family_id,
        'X-Ig-Android-Id': android_id,
        'X-Ig-App-Id': APP_ID,
        'X-Mid': x_mid,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    payload = {
        "phone_id": family_id,
        "guid": device_id,
        "device_id": android_id,
        "email": email,
        "waterfall_id": waterfall_id,
        "auto_confirm_only": "false"
    }

    encoded = urllib.parse.quote(json.dumps(payload))
    response = requests.post(
        "https://i.instagram.com/api/v1/accounts/send_verify_email/",
        data=f"signed_body={SIGNATURE}.{encoded}",
        headers=headers,
        proxies=get_proxy()
    )

    if response.json().get("status") != "ok":
        print(f"[×] Failed to send verification email to {email}")
        return

    code = get_verification_code(token)
    if not code:
        print("[×] Failed to retrieve verification code.")
        return

    confirm_payload = {
        "code": code,
        "email": email,
        "device_id": android_id,
        "waterfall_id": waterfall_id
    }

    response = requests.post(
        "https://i.instagram.com/api/v1/accounts/check_confirmation_code/",
        data={"signed_body": f"{SIGNATURE}.{json.dumps(confirm_payload)}"},
        headers=headers,
        proxies=get_proxy()
    )

    signup_code = response.json().get("signup_code")
    if not signup_code:
        print("[×] Failed to get signup code.")
        return

    create_payload = {
        'is_secondary_account_creation': 'false',
        'jazoest': jazoest,
        'tos_version': 'row',
        'phone_id': family_id,
        'enc_password': PASSWORD,
        'username': username,
        'first_name': faker.first_name(),
        'day': '14',
        'adid': adid,
        'guid': device_id,
        'year': '1993',
        'device_id': android_id,
        '_uuid': device_id,
        'email': email,
        'month': '10',
        'force_sign_up_code': signup_code,
        'one_tap_opt_in': 'true'
    }

    encoded_create = urllib.parse.quote(json.dumps(create_payload))
    response = requests.post(
        "https://i.instagram.com/api/v1/accounts/create/",
        data=f"signed_body={SIGNATURE}.{encoded_create}",
        headers=headers,
        proxies=get_proxy()
    )

    if '"account_created":true' in response.text:
        print(f"[✓] Created account: {email} | {PASSWORD} | {username}")
        with open("accounts.txt", "a") as f:
            f.write(f"{email}:{PASSWORD}:{username}\n")
    else:
        print(f"[×] Failed to create account: {email}")
        print(response.text)

def main():
    try:
        count = int(input("[+] How Many Accounts to Create: "))
    except ValueError:
        print("Invalid number.")
        return

    for _ in range(count):
        email, token = get_emails()
        create_account(email, token)

if __name__ == "__main__":
    main()
