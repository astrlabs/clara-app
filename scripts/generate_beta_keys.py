import firebase_admin
from firebase_admin import credentials, firestore
import random
import string
import sys
import os

# To run this, you need your firebase credentials path or service account dict.
# It will try to use the ones from the app's environment.

def generate_key(length=8):
    """Generate a random alphanumeric key."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def main(count=10):
    # Try to find credentials
    cred_path = "clara-companion-fe6a8-firebase-adminsdk-fbsvc-fca8258bfb.json"
    if not os.path.exists(cred_path):
        print(f"Error: Could not find firebase credentials at {cred_path}")
        print("Please ensure the service account JSON is in the root directory.")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    generated_keys = []
    
    print(f"Generating {count} unique access keys...")
    
    batch = db.batch()
    for _ in range(count):
        new_key = generate_key()
        # Ensure uniqueness (simple check, for large scale would need more)
        ref = db.collection("beta_keys").document(new_key)
        batch.set(ref, {
            "used": False,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "generatedBy": "script"
        })
        generated_keys.append(new_key)
    
    batch.commit()
    
    print("\n--- GENERATED KEYS ---")
    for k in generated_keys:
        print(k)
    print("----------------------\n")
    print(f"Successfully uploaded {count} keys to Firestore.")

if __name__ == "__main__":
    num_keys = 10
    if len(sys.argv) > 1:
        try:
            num_keys = int(sys.argv[1])
        except ValueError:
            pass
    main(num_keys)
