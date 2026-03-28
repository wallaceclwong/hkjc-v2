from fastapi import APIRouter
from pydantic import BaseModel
from firebase_admin import messaging as firebase_messaging

router = APIRouter()

class SubscribeRequest(BaseModel):
    token: str
    topic: str = "high_confidence_bets"

@router.post("/subscribe")
async def subscribe_to_alerts(request: SubscribeRequest):
    try:
        response = firebase_messaging.subscribe_to_topic([request.token], request.topic)
        return {
            "success": True, 
            "results": {
                "success_count": response.success_count,
                "failure_count": response.failure_count
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
