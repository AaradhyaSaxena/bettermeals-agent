import firebase_admin
from firebase_admin import credentials, firestore, storage
from src.bettermeals.config.secrets_manager import secrets_manager

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK, handling re-initialization gracefully.
    This function is the single source of initialization for the app.
    It configures both Firestore and Storage.
    """
    print("Starting Firebase initialization...")
    
    if not firebase_admin._apps:
        try:
            firebase_credentials = secrets_manager.get_firebase_credentials()
            cred = credentials.Certificate(firebase_credentials)
            
            # Get storage bucket from secrets manager with fallback
            storage_bucket = secrets_manager.get_secret("FIREBASE_STORAGE_BUCKET", "bettermeals-f47b8.firebasestorage.app")
            
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
            print(f"Firebase initialized successfully with bucket: {storage_bucket}")
            
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise ValueError(f"Error initializing Firebase credentials: {e}")
    else:
        print("Firebase app already initialized, skipping...")
    firestore_client = firestore.client()
    print("Firestore client created successfully")
    return firestore_client

def get_storage_bucket():
    """
    Returns the default Firebase Storage bucket.
    Ensures Firebase app is initialized before returning the bucket.
    """
    # initialize_firebase() is idempotent and will handle the initialization check.
    initialize_firebase()
    return storage.bucket() 