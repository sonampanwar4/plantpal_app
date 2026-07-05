from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates

from datetime import date, timedelta
from logging import getLogger
from sqlalchemy.orm import Session
#  local
from database import get_db
from repositories.plant_repo import get_user_plants
from schemas.user import ResponseUser
from schemas.care_task import PlantCareTaskCreate, PlantCareTaskUpdate
from utils.helper import redirect_with_message
# services
from services.user_service import get_current_user_service
from services.care_task_service import (
    get_tasks_statistics_service, update_care_task_service,
    create_care_task_service, complete_task_service,
    get_task_by_id_service
)


logger = getLogger(__name__)
# If you have a global templates instance, import it instead
templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix="/dashboard", tags=['Dashboard'])

@router.get('/')
async def dashboard(
        request: Request,
        user: ResponseUser = Depends(get_current_user_service),
        db: Session = Depends(get_db)
):
    """Render the main dashboard page with user's plants and task data."""
    if not user:
        raise redirect_with_message(
            "/login","Please log in to access this page.",
            "error",303
        )

    # Get user's plants
    plants = get_user_plants(db, user.id)
    # Get task statistics
    task_statistics = get_tasks_statistics_service(db, user.id)
    print(task_statistics)
    print(date.today())
    message = request.cookies.get("message")
    message_type = request.cookies.get("message_type")

    context = {
        'request': request,
        'user': user,
        'plants': plants,
        'task_statistics': task_statistics,
        'message': message,
        'message_type': message_type
    }
    response = templates.TemplateResponse('dashboard_page.html', context=context)
    response.delete_cookie("message")
    response.delete_cookie("message_type")
    return response


@router.post('/tasks')
async def create_task(
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service),
        task_data: PlantCareTaskCreate = Depends(PlantCareTaskCreate.as_form)
):
    """Create a new care task."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        # Set the due date on the task data
        task_data.due_date = date.today()
        task_data.user_id = user.id
        created_task = create_care_task_service(db, task_data, user.id)

        if not created_task:
            raise HTTPException(
                status_code=400,
                detail="Failed to create task - plant may not exist or you don't have permission"
            )
        return created_task
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid data: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post('/tasks/{task_id}/complete')
async def complete_task(
        task_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Mark a task as completed."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        body = await request.json()
        is_completed = body.get("is_completed", True)
        complete_task_service(db, task_id, user.id, is_completed)
        return {"message": "Task status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task status: {str(e)}")



@router.put('/tasks/{task_id}')
async def update_task(
        task_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service),
        task_data: PlantCareTaskUpdate = Depends(PlantCareTaskUpdate.as_form)
):
    """Update an existing care task."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        if task_data.frequency_days and task_data.frequency_days > 0:
            task_data.due_date = date.today() + timedelta(days=task_data.frequency_days)


        # Set the due date on the task data
        task_data.user_id = user.id
        task_data.id = task_id
        # You'll need to create this function in your care_task_service
        updated_task = update_care_task_service(db, task_id, task_data, user.id)

        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found or unauthorized")

        return updated_task

    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.get('/tasks/{task_id}')
async def get_task(
        task_id: int,
        db: Session = Depends(get_db),
        user: ResponseUser = Depends(get_current_user_service)
):
    """Return a single task as JSON for editing."""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")


    task = get_task_by_id_service(db, task_id, user.id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    return task
