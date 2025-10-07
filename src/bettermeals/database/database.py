from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore
from src.bettermeals.database.firebase_init import initialize_firebase
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """Database layer for managing health-related data in Firestore"""
    
    def __init__(self):
        """Initialize database connection"""
        try:
            logger.info("Initializing database connection")
            self.db = initialize_firebase()
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            raise

    def find_user_by_phone(self, phone_number: str):
        """Find user by WhatsApp phone number"""
        try:
            logger.info(f"Searching for user with phone number: {phone_number}")
            users_ref = self.db.collection("user")
            q = users_ref.where("whatsappNumber", "==", phone_number).limit(1)
            docs = list(q.stream())
            
            if not docs:
                logger.info(f"No user found with phone number: {phone_number}")
                return None
                
            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id
            logger.info(f"Found user: {doc.id} for phone number: {phone_number}")
            return data
            
        except Exception as e:
            logger.error(f"Error finding user by phone {phone_number}: {str(e)}")
            raise

    def get_household_data(self, household_id: str):
        """Get household data by ID"""
        try:
            logger.info(f"Retrieving household data for ID: {household_id}")
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id).get()
            
            if not doc.exists:
                logger.info(f"No household found with ID: {household_id}")
                return None
                
            data = doc.to_dict()
            data["id"] = doc.id
            logger.info(f"Successfully retrieved household data for ID: {household_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving household data for ID {household_id}: {str(e)}")
            raise

    def update_household_data(self, household_id: str, data: dict):
        """Update household data"""
        try:
            logger.info(f"Updating household data for ID: {household_id}")
            logger.debug(f"Update data: {data}")
            
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id)
            doc.update(data)
            
            logger.info(f"Successfully updated household data for ID: {household_id}")
            
        except Exception as e:
            logger.error(f"Error updating household data for ID {household_id}: {str(e)}")
            raise



# -------------------- Singleton Instance -------------------- #
_db_instance = None

def get_db() -> Database:
    """Get singleton instance of Database"""
    global _db_instance
    try:
        if _db_instance is None:
            logger.info("Creating new database instance")
            _db_instance = Database()
        return _db_instance
    except Exception as e:
        logger.error(f"Failed to get database instance: {str(e)}")
        raise
