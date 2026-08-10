import os
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()


import json

def init_firebase():
    if not firebase_admin._apps:
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "services/auth/config/firebase-credentials.json")
        
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from FIREBASE_CREDENTIALS_JSON")
        elif os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from local credentials file")
        else:
            firebase_admin.initialize_app()
            print("✅ Firebase initialized using Application Default Credentials")
    else:  
        print("⚠️ Firebase already initialized")
