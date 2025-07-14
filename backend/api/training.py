from fastapi import APIRouter, BackgroundTasks
from training.fine_tune import fine_tune
from utils.email_notify import notify_training_complete

router = APIRouter()

@router.post("/start-training/")
async def start_training(background_tasks: BackgroundTasks):
    background_tasks.add_task(fine_tune)
    return {"status": "Training started"}

@router.get("/status/")
async def training_status():
    return {"status": "Training log check not implemented"}

@router.post("/notify/")
async def test_notification():
    notify_training_complete(
        to_email="shivam.s@appgallop.com",
        model_name="support-model-v1",
        details="Test notification after training"
    )
    return {"status": "Notification sent"}