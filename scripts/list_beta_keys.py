import firebase_admin
from firebase_admin import credentials, firestore
import os

def main():
    # Try to find credentials
    cred_path = "clara-companion-fe6a8-firebase-adminsdk-fbsvc-fca8258bfb.json"
    if not os.path.exists(cred_path):
        print(f"Error: Could not find firebase credentials at {cred_path}")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    # Query for unused keys
    keys_ref = db.collection("beta_keys")
    query = keys_ref.where("used", "==", False).order_by("createdAt", direction=firestore.Query.DESCENDING)
    docs = query.stream()
    
    unused_keys = []
    for doc in docs:
        unused_keys.append(doc.id)
    
    if not unused_keys:
        print("\nNo unused beta keys found. Run 'python scripts/generate_beta_keys.py' to create some!")
    else:
        print(f"\n--- FOUND {len(unused_keys)} UNUSED KEYS ---")
        for k in unused_keys:
            print(k)
        print("-------------------------------\n")

if __name__ == "__main__":
    main()
