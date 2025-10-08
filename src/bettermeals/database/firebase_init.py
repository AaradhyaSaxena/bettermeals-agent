import firebase_admin
from firebase_admin import credentials, firestore, storage

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK, handling re-initialization gracefully.
    This function is the single source of initialization for the app.
    It configures both Firestore and Storage.
    """
    if not firebase_admin._apps:
        key_path = "src/bettermeals/database/config/bettermeals_firebase_key.json"

        try:
            cred = credentials.Certificate(key_path)
        except FileNotFoundError:
            # Re-raise with a more helpful message
            raise FileNotFoundError(
                f"Firebase credentials not found at '{key_path}'. "
                f"Ensure the file exists and the script is run from the project root."
            )

        firebase_admin.initialize_app(cred, {
            'storageBucket': 'bettermeals-f47b8.firebasestorage.app'
        })

    return firestore.client()

def get_storage_bucket():
    """
    Returns the default Firebase Storage bucket.
    Ensures Firebase app is initialized before returning the bucket.
    """
    # initialize_firebase() is idempotent and will handle the initialization check.
    initialize_firebase()
    return storage.bucket() 