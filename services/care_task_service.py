from sqlalchemy.orm import Session
from models.care_task import PlantCareTask
from schemas.care_task import (
    PlantCareTaskCreate, PlantCareTaskUpdate
)
from repositories.care_task_repo import (
    create_care_task, update_care_task, delete_care_task,
    get_all_completed_tasks, get_all_completed_tasks_by_date, complete_task,
    get_task_by_id, get_user_all_active_tasks
)
from typing import Optional
from datetime import date, timedelta


# Task CRUD operations with enhanced responses
def create_care_task_service(db: Session,
                             care_task: PlantCareTaskCreate,
                             user_id: int) -> PlantCareTask | None:

    """Service layer for creating a new care task with enhanced response."""
    return create_care_task(db, care_task, user_id)


def update_care_task_service(db: Session,
                             task_id: int,
                             task_update: PlantCareTaskUpdate,
                             user_id: int) -> PlantCareTask | None:
    """Service layer for updating a care task with enhanced response."""
    return update_care_task(db, task_id, task_update, user_id)

def get_task_by_id_service(db: Session,
                             task_id: int,
                             user_id: int) -> Optional[PlantCareTask]:
    return get_task_by_id(db=db, task_id=task_id, user_id=user_id)

def delete_care_task_service(db: Session, task_id: int, user_id: int) -> bool:
    """Service layer for deleting a care task."""
    return delete_care_task(db, task_id, user_id)


# Task Completion Service for Frontend
def complete_task_service(db: Session, task_id: int, user_id: int, is_completed: bool) -> bool:
    """
    Service layer for completing a task from frontend. Creates task completion history if is_completed is True.
    """
    if is_completed:
        return complete_task(db, task_id, user_id)
    return False

# all completed tasks
def get_all_completed_tasks_by_date_service(db: Session, user_id: int, target_date: date) -> list:
    """Service layer for getting all completed tasks by date."""
    return get_all_completed_tasks_by_date(db, user_id, target_date)

def get_all_completed_tasks_service(db: Session, user_id: int):
    """Service layer for getting all delayed tasks."""
    return get_all_completed_tasks(db=db, user_id=user_id)

# Task statistics
def get_tasks_statistics_service(db: Session, user_id: int) -> dict:
    """Service layer for getting all care tasks status."""
    completed_tasks = get_all_completed_tasks_service(db, user_id)

    todays, upcoming, delayed = [], [], []
    today = date.today()
    active_tasks = get_user_all_active_tasks(db=db, user_id=user_id)
    if active_tasks:
        for task in active_tasks:
            if task.due_date == today: #TODO
                upcoming.append(task)
            if task.due_date == today:
                todays.append(task)
            if task.due_date < today:
                delayed.append(task)
        return {
            "todays_tasks": todays,
            "completed_tasks": completed_tasks,
            "delayed_tasks": delayed,
            "upcoming_tasks": upcoming
        }
    return {}


def generate_care_tasks_context(db: Session, user_id: int) -> list:
    stats = get_tasks_statistics_service(db, user_id)
    context = []
    for task_type, tasks in stats.items():
        context.append({
            task_type: [task.title for task in tasks]
        })

    return context

def get_user_all_active_tasks_service(db: Session, user_id: int, limit: int=5) -> list:
    return get_user_all_active_tasks(db, user_id, limit=limit)