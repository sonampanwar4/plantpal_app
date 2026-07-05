from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from schemas.plant import PlantUpdate, PlantCreate
from services.plant_service import (
    update_plant_service, get_plant_service,
    delete_plant_service, create_user_plant_service

)
from database import get_db
from services.user_service import get_current_user_service
from schemas.user import ResponseUser
from fastapi.templating import Jinja2Templates
from logging import getLogger
from utils.helper import redirect_with_message

logger = getLogger(__name__)
router = APIRouter(prefix="/plants", tags=['Plants'])
templates = Jinja2Templates(directory="templates")


def render_plant_form(
    request: Request,
    title: str,
    plant=None,
    action="/plants"
):
    context = {
        "request": request,
        "title": title,
        "plant": plant,
        "action": action
    }
    response = templates.TemplateResponse("plant_form.html", context)
    response.delete_cookie("message")
    response.delete_cookie("message_type")
    return response

@router.get("/")
async def plant_form(
    request: Request,
    user: ResponseUser = Depends(get_current_user_service),
):
    if not user:
        return redirect_with_message(
            "/login",
            "Please log in to access this page.",
            "error",
        )

    return render_plant_form(request, "Add New Plant")

@router.post("/")
async def add_plant(
        plant_data: PlantCreate,
        user: ResponseUser = Depends(get_current_user_service),
        db: Session = Depends(get_db)
):
    """Handle adding a new plant to the user's collection."""
    if not user:
        return redirect_with_message(
            url="/login", status_code=303, message="Please log in to access this page.", message_type="error"
        )

    try:
        print(plant_data)
        plant = create_user_plant_service(db, plant_data, user.id)
        print(plant.name)
        if plant:
            return redirect_with_message(
                "/dashboard",
                f"Successfully added {plant_data.name}!",
                status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            raise

    except Exception as e:
        logger.error(f"Error adding plant: {e}")
        return redirect_with_message(
            "/",
            "Failed to add plant. Please try again.",
            "error",
        )

@router.get("/update/{plant_id}")
async def update_plant_form(
    plant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user_service),
):
    if not user:
        return redirect_with_message(
            url="/login", status_code=303, message="Please log in to access this page.", message_type="error"
        )
    plant = get_plant_service(db, plant_id, user.id)
    if not plant:
        return redirect_with_message(
            "/",
            "Failed to update plant. Please try again.",
            "error",
        )

    return render_plant_form(request, "Update Your Plant", plant, action=f"/plants/update/{plant_id}")

@router.put("/update/{plant_id}")
async def update_plant(
    plant_id: int,
    plant_data: PlantUpdate,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user_service),
):
    if not user:
        return redirect_with_message(
            url="/login",
            status_code=status.HTTP_303_SEE_OTHER,
            message="Please log in to access this page.",
            message_type="error"
        )
    try:
        updated = update_plant_service(db, plant_id, plant_data, user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Plant not found")

        return redirect_with_message(
            "/dashboard",
            f"Updated {plant_data.name}!",
            status_code=status.HTTP_303_SEE_OTHER
        )

    except Exception as e:
        logger.error(f"Error updating plant: {e}")
        raise HTTPException(status_code=500, detail="Failed to update plant")


@router.delete("/delete/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plant(
    plant_id: int,
    db: Session = Depends(get_db),
    user: ResponseUser = Depends(get_current_user_service),
):
    if not user:
        return redirect_with_message(
            url="/login", status_code=303, message="Please log in to access this page.", message_type="error"
        )
    deleted = delete_plant_service(db, user.id, plant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plant not found")

    return redirect_with_message(
        "/dashboard",
        "Deleted your plant!",
        status_code=status.HTTP_303_SEE_OTHER
    )

