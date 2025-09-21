import os
import flexprice
from fastapi.responses import JSONResponse

# Initialize Flexprice
FLEXPRICE_API_KEY = os.getenv("FLEXPRICE_API_KEY", "your_flexprice_api_key_here")
flexprice.api_key = FLEXPRICE_API_KEY

def track_documents_checked(user_id: str, quantity: int):
    """
    Track usage when documents are uploaded.
    """
    try:
        flexprice.track_usage(
            user_id=user_id,
            metric="documents_checked",
            quantity=quantity
        )
    except Exception as e:
        print(f"[Flexprice] Error tracking documents_checked: {e}")

def track_reports_generated(user_id: str, quantity: int = 1):
    """
    Track usage when a report is generated.
    """
    try:
        flexprice.track_usage(
            user_id=user_id,
            metric="reports_generated",
            quantity=quantity
        )
    except Exception as e:
        print(f"[Flexprice] Error tracking reports_generated: {e}")

def get_user_usage(user_id: str):
    """
    Fetch usage data for a user/submission.
    Returns JSON response or error message.
    """
    try:
        usage = flexprice.get_usage(user_id=user_id)
        return usage
    except Exception as e:
        print(f"[Flexprice] Error fetching usage: {e}")
        return JSONResponse(status_code=500, content={"message": f"Fetch usage failed: {e}"})
