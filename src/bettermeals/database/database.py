from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud import firestore
from src.bettermeals.database.firebase_init import initialize_firebase
import logging
import json

# Configure logging
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

    #######################################
    ######## HOUSEHOLD ##########
    #######################################

    def find_user_by_phone(self, phone_number: str):
        """Find user by WhatsApp phone number"""
        try:
            logger.debug(f"Searching for user with phone number: {phone_number}")
            users_ref = self.db.collection("user")
            q = users_ref.where("whatsappNumber", "==", phone_number).limit(1)
            docs = list(q.stream())
            
            if not docs:
                logger.debug(f"No user found with phone number: {phone_number}")
                return None
                
            doc = docs[0]
            data = doc.to_dict()
            data["id"] = doc.id
            logger.debug(f"Found user: {doc.id} for phone number: {phone_number}")
            return data
            
        except Exception as e:
            logger.error(f"Error finding user by phone {phone_number}: {str(e)}")
            raise

    def get_household_data(self, household_id: str):
        """Get household data by ID"""
        try:
            logger.debug(f"Retrieving household data for ID: {household_id}")
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id).get()
            
            if not doc.exists:
                logger.debug(f"No household found with ID: {household_id}")
                return None
                
            data = doc.to_dict()
            data["id"] = doc.id
            logger.debug(f"Successfully retrieved household data for ID: {household_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving household data for ID {household_id}: {str(e)}")
            raise

    def update_household_data(self, household_id: str, data: dict):
        """Update household data"""
        try:
            logger.debug(f"Updating household data for ID: {household_id}")
            logger.debug(f"Update data: {data}")
            
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id)
            doc.update(data)
            
            logger.debug(f"Successfully updated household data for ID: {household_id}")
            
        except Exception as e:
            logger.error(f"Error updating household data for ID {household_id}: {str(e)}")
            raise

    #######################################
    ######## ONBOARDING WORKFLOW ##########
    #######################################

    def save_onboarding_message(self, phone_number: str, message_data: Dict[str, Any]) -> bool:
        """Save individual onboarding message to database"""
        try:
            logger.debug(f"Saving onboarding message for phone: {phone_number}")
            
            # Create or get onboarding_messages collection
            messages_ref = self.db.collection("onboarding_messages")
            
            # Add timestamp and phone number to message data
            message_data["phone_number"] = phone_number
            message_data["timestamp"] = datetime.now()
            
            # Add the message
            messages_ref.add(message_data)
            
            logger.debug(f"Successfully saved onboarding message for phone: {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving onboarding message for phone {phone_number}: {str(e)}")
            return False

    def get_onboarding_messages(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get all onboarding messages for a phone number"""
        try:
            logger.debug(f"Getting onboarding messages for phone: {phone_number}")
            
            messages_ref = self.db.collection("onboarding_messages")
            # Use only where clause to avoid index requirement, then sort in Python
            q = messages_ref.where("phone_number", "==", phone_number)
            docs = list(q.stream())
            
            messages = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                messages.append(data)
            
            # Sort by timestamp in Python to avoid Firestore index requirement
            messages.sort(key=lambda x: x.get("timestamp", datetime.min))
            
            logger.debug(f"Retrieved {len(messages)} onboarding messages for phone: {phone_number}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting onboarding messages for phone {phone_number}: {str(e)}")
            return []

    def save_final_onboarding_data(self, phone_number: str, onboarding_data: Dict[str, Any]) -> bool:
        """Save final onboarding data to household collection"""
        try:
            logger.info(f"Saving final onboarding data for phone: {phone_number}")
            
            # First find the user to get household_id
            user = self.find_user_by_phone(phone_number)
            if user is None:
                logger.warning(f"No user found for phone: {phone_number}, terminating onboarding.")
                return False
                
            household_id = user.get("householdId")
            if household_id is None:
                logger.warning(f"No household_id found for user: {phone_number}, terminating onboarding.")
                return False
            
            # Update household with final onboarding data
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id)
            doc.update({"onboarding": onboarding_data})
            
            logger.info(f"Successfully saved final onboarding data to household {household_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving final onboarding data for phone {phone_number}: {str(e)}")
            return False

    #######################################
    ######## GENERIC WORKFLOW REF #########
    #######################################

    def save_workflow_message(self, phone_number: str, message_data: Dict[str, Any], collection_name: str):
        """Save workflow message to database"""
        try:
            logger.debug(f"Saving workflow message for phone: {phone_number}")
            messages_ref = self.db.collection(collection_name)

            message_data["phone_number"] = phone_number
            message_data["timestamp"] = datetime.now()

            messages_ref.add(message_data)
            logger.debug(f"Successfully saved workflow message for phone: {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error saving workflow message for phone {phone_number}: {str(e)}")
            return False

    def get_workflow_messages(self, phone_number: str, collection_name: str) -> List[Dict[str, Any]]:
        """Get all workflow messages for a phone number"""
        try:
            logger.debug(f"Getting workflow messages for phone: {phone_number}")
            messages_ref = self.db.collection(collection_name)
            q = messages_ref.where("phone_number", "==", phone_number)
            docs = list(q.stream())
            messages = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                messages.append(data)
            messages.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            return messages
        except Exception as e:
            logger.error(f"Error getting workflow messages for phone {phone_number}: {str(e)}")
            return []

    def save_final_workflow_data(self, phone_number: str, workflow_data: Dict[str, Any], collection_name: str) -> bool:
        """Save final workflow data to database"""
        try:
            logger.debug(f"Saving final workflow data for phone: {phone_number}")
            workflow_ref = self.db.collection(collection_name)
            workflow_ref.add(workflow_data)
            logger.debug(f"Successfully saved final workflow data for phone: {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Error saving final workflow data for phone {phone_number}: {str(e)}")
            return False

    def weeklyplan_completion_status_hld(self, household_id: str) -> bool:
        """Update weekly plan status for a household"""
        try:
            current_week_num = datetime.now().isocalendar()[1]
            weekly_plan_status = {
                "status": "approved",
                "week": current_week_num
            }
            logger.debug(f"Updating weekly plan status for household: {household_id}, week: {current_week_num}")
            household_ref = self.db.collection("household")
            doc = household_ref.document(household_id)
            doc.update({"weekly_plan": weekly_plan_status})
            logger.debug(f"Successfully saved weekly plan status for household: {household_id}, week: {current_week_num}")
            return True
        except Exception as e:
            logger.error(f"Error updating weekly plan status for household {household_id}: {str(e)}")
            return False


# -------------------- Singleton Instance -------------------- #
_db_instance = None
_db_lock = None

def get_db() -> Database:
    """Get singleton instance of Database"""
    global _db_instance, _db_lock
    
    if _db_lock is None:
        import threading
        _db_lock = threading.Lock()
    
    if _db_instance is None:
        with _db_lock:
            # Double-check pattern to avoid race conditions
            if _db_instance is None:
                try:
                    logger.info("Creating new database instance")
                    _db_instance = Database()
                except Exception as e:
                    logger.error(f"Failed to create database instance: {str(e)}")
                    raise
    
    return _db_instance
