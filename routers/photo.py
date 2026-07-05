from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session

from utils.markdown_converter import markdown_to_html
from utils.helper import redirect_with_message
from database import get_db
from services.plant_service import get_user_plants_service
from services.user_service import get_current_user_service
from schemas.user import ResponseUser
from services.photo_service import (
    get_user_photos_with_diagnoses_service, delete_user_photo_service,
    get_user_photo_by_id_service, get_latest_photo_diagnosis_service,
    get_analysis_statistics_service
)
from schemas.ai_bot import UserChatRequestModel
from services.chat_handler_service import handle_ai_chat_service
from logging import getLogger

logger = getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/photo_gallery", response_class=HTMLResponse)
async def photo_gallery(
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Display user's photo gallery with diagnoses."""
    if not user:
        return redirect_with_message(
            "/login",
            "Please log in to access this page.",
            "error",
        )

    try:
        # Get user's photos with diagnoses
        photos_with_diagnoses = get_user_photos_with_diagnoses_service(db, user.id, limit=50)

        # Get analysis statistics
        stats = get_analysis_statistics_service(db, user.id)

        return templates.TemplateResponse("photo_gallery.html", {
            "request": request,
            "user": user,
            "photos_with_diagnoses": photos_with_diagnoses,
            "stats": stats
        })

    except Exception as e:
        logger.exception(f"Error in photo_gallery: {str(e)}")
        return templates.TemplateResponse("photo_gallery.html", {
            "request": request,
            "user": user,
            "photos_with_diagnoses": [],
            "user_plants": [],
            "stats": {},
            "error": "Failed to load photo gallery"
        })


@router.post("/analyze_photo/{photo_id}")
async def analyze_photo(
        photo_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Analyze a specific photo with AI."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        # Verify photo belongs to user
        photo = get_user_photo_by_id_service(db, photo_id, user.id)
        if not photo:
            return JSONResponse(
                status_code=404,
                content={"error": "Photo not found"}
            )
        user_data = UserChatRequestModel(
            user_id=user.id,
            input_text=photo.user_query,
            plant_id=photo.plant_id,
            photo_file=photo.image_path,
            chat_type='diagnosis'
        )
        # Analyze photo with RAG
        analysis_result = await handle_ai_chat_service(db, user_data)

        # Convert markdown to HTML for the response
        bot_response_html = markdown_to_html(analysis_result)

        return JSONResponse(content={
            "success": True,
            "analysis": bot_response_html,
            "photo_id": photo_id
        })

    except Exception as e:
        logger.exception("f❌ Analysis failed: {str(e)}")
        error_response = f"❌ Analysis failed: {str(e)}"

        return JSONResponse(
            status_code=500,
            content={"error": error_response}
        )


@router.delete("/delete_photo/{photo_id}")
async def delete_photo(
        photo_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Delete a photo and its associated data."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        success = delete_user_photo_service(db, photo_id, user.id)

        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Photo deleted successfully"
            })
        else:
            return JSONResponse(
                status_code=404,
                content={"error": "Photo not found"}
            )

    except Exception as e:
        logger.error(f"Error deleting photo {photo_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to delete photo"}
        )


@router.get("/{photo_id}/diagnosis")
async def get_photo_diagnosis_endpoint(
        photo_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Get diagnosis for a specific photo."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        logger.info(photo_id)
        # Get diagnosis
        diagnosis = get_latest_photo_diagnosis_service(db, photo_id, user.id)
        print(diagnosis)
        if diagnosis:
            return JSONResponse(content={
                "success": True,
                "diagnosis": {
                    "id": diagnosis.id,
                    "diagnosis_text": diagnosis.diagnosis_text,
                    "confidence_score": diagnosis.confidence_score,
                    "identified_issues": diagnosis.identified_issues,
                    "recommended_actions": diagnosis.recommended_actions,
                    "treatment_outcome": diagnosis.treatment_outcome,
                    "created_at": diagnosis.created_at.isoformat()
                }
            })
        else:
            return JSONResponse(content={
                "success": True,
                "diagnosis": None,
                "message": "No diagnosis available for this photo"
            })

    except Exception as e:
        logger.error(f"Error getting diagnosis for photo {photo_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get diagnosis"}
        )


# API endpoints for integration with analyse_chat_2 system
@router.get("/api/user_photos")
async def get_user_photos_api(
        limit: int = 20,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """API endpoint to get user's photos."""
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"}
        )

    try:
        photos_with_diagnoses = get_user_photos_with_diagnoses_service(db, user.id, limit=limit)

        photos_data = []
        for item in photos_with_diagnoses:
            photo_data = {
                "id": item.photo.id,
                "image_path": item.photo.image_path,
                "original_filename": item.photo.original_filename,
                "upload_context": item.photo.upload_context,
                "diagnosis_status": item.photo.diagnosis_status,
                "created_at": item.photo.created_at.isoformat(),
                "plant_name": item.plant_name,
                "has_diagnosis": item.diagnosis is not None,
                "thumbnail_url": f"/static/uploads/thumbnails/thumb_{item.photo.image_path.split('/')[-1]}"
            }

            if item.diagnosis:
                photo_data["diagnosis"] = {
                    "confidence_score": item.diagnosis.confidence_score,
                    "treatment_outcome": item.diagnosis.treatment_outcome,
                    "created_at": item.diagnosis.created_at.isoformat()
                }

            photos_data.append(photo_data)

        return JSONResponse(content={
            "success": True,
            "photos": photos_data
        })

    except Exception as e:
        logger.error(f"Error in get_user_photos_api: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get photos"}
        )
