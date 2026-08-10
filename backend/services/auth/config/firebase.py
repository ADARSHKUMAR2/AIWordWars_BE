import os
import json
import base64
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

load_dotenv()


def init_firebase():
    if not firebase_admin._apps:
        # Try base64-encoded credentials first (for Cloud Run)
        cred_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "services/auth/config/firebase-credentials.json")
        
        if cred_base64:
            try:
                # Decode base64 and parse JSON
                decoded_json = base64.b64decode(cred_base64).decode('utf-8')
                cred_dict = json.loads(decoded_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print(f"✅ Firebase initialized from FIREBASE_CREDENTIALS_BASE64 (project: {cred_dict.get('project_id', 'unknown')})")
            except Exception as e:
                print(f"❌ Failed to initialize Firebase from base64: {e}")
                raise
        elif cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print(f"✅ Firebase initialized from FIREBASE_CREDENTIALS_JSON (project: {cred_dict.get('project_id', 'unknown')})")
        elif os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized from local credentials file")
        else:
            firebase_admin.initialize_app()
            print("✅ Firebase initialized using Application Default Credentials")
    else:  
        print("⚠️ Firebase already initialized")
