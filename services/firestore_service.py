import os
from google.cloud import firestore
from config.settings import Config
from loguru import logger

class FirestoreService:
    def __init__(self):
        try:
            self.db = Config.get_firestore_client()
            logger.info("✅ Firestore Service Initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {e}")
            self.db = None

    def upsert(self, collection: str, doc_id: str, data: any):
        """Standard upsert for a single document (handles Pydantic models)."""
        if not self.db: return
        
        try:
            # Handle Pydantic models if passed
            if hasattr(data, "model_dump"):
                doc_data = data.model_dump()
            elif hasattr(data, "dict"):
                doc_data = data.dict()
            else:
                doc_data = data
                
            self.db.collection(collection).document(doc_id).set(doc_data)
            return True
        except Exception as e:
            logger.error(f"Firestore Upsert Error [{collection}/{doc_id}]: {e}")
            return False

    def batch_upsert(self, collection: str, data_map: dict):
        """Batch upsert for multiple documents."""
        if not self.db: return
        
        try:
            batch = self.db.batch()
            for doc_id, data in data_map.items():
                doc_ref = self.db.collection(collection).document(doc_id)
                # Handle Pydantic models
                if hasattr(data, "model_dump"):
                    doc_data = data.model_dump()
                else:
                    doc_data = data
                batch.set(doc_ref, doc_data)
            batch.commit()
            return True
        except Exception as e:
            logger.error(f"Firestore Batch Upsert Error [{collection}]: {e}")
            return False

    def get_document(self, collection: str, doc_id: str):
        """Fetches a single document."""
        if not self.db: return None
        
        try:
            doc = self.db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Firestore Get Error [{collection}/{doc_id}]: {e}")
            return None

    def get_latest(self, collection: str, order_by: str = "timestamp", limit: int = 1):
        """Fetches the latest document(s) based on a field."""
        if not self.db: return None
        
        try:
            query = self.db.collection(collection).order_by(order_by, direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.stream()
            results = [doc.to_dict() for doc in docs]
            return results[0] if results and limit == 1 else results
        except Exception as e:
            logger.error(f"Firestore Get latest Error [{collection}]: {e}")
            return None

    def query(self, collection: str, filters: list = None, order_by: str = None, limit: int = None):
        """Generic query method."""
        if not self.db: return []
        
        try:
            ref = self.db.collection(collection)
            if filters:
                for field, op, val in filters:
                    ref = ref.where(field, op, val)
            if order_by:
                # Handle 'field' or ('field', 'desc')
                if isinstance(order_by, tuple):
                    ref = ref.order_by(order_by[0], direction=order_by[1])
                else:
                    ref = ref.order_by(order_by)
            if limit:
                ref = ref.limit(limit)
                
            docs = ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Firestore Query Error [{collection}]: {e}")
            return []
