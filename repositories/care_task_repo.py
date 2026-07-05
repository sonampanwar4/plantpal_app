from sqlalchemy.orm import Session
from datetime import date, timedelta
from models.care_task import PlantCareTask
from schemas.care_task import PlantCareTaskCreate, PlantCareTaskUpdate
from models.care_task import TaskCompletionHistory
from models.plant import Plant
from typing import List, Optional
from logging import getLogger

logger = getLogger(__name__)

# CRUD operation for Plant care Task
def create_care_task(db: Session, care_task: PlantCareTaskCreate, user_id: int) -> Optional[PlantCareTask]:
    """Create a new care task in the database with user ownership validation."""
    # Verify plant ownership
    plant = db.query(Plant).filter(Plant.id == care_task.plant_id, Plant.user_id == user_id).first()
    if plant:
        try:
            db_care_task = PlantCareTask(**care_task.model_dump())
            db.add(db_care_task)
            db.commit()
            db.refresh(db_care_task)
            return db_care_task
        except Exception as e:
            logger.error(f"Database error: {e}")
    return None

def get_task_by_id(db: Session,
                     task_id: int,
                    user_id: int) -> Optional[PlantCareTask]:
    try:
        return db.query(PlantCareTask).filter(
            PlantCareTask.id == task_id, PlantCareTask.user_id == user_id
        ).first()
    except Exception:
        logger.exception(f"No task found by ID {task_id}")
        return None

def update_care_task(db: Session,
                     task_id: int,
                     task_update: PlantCareTaskUpdate, user_id: int) -> Optional[PlantCareTask]:
    """Update a care task."""
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()

    if db_task:
        try:
            task_update.updated_at = date.today()
            update_data = task_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_task, field, value)
            db.commit()
            db.refresh(db_task)
            return db_task
        except Exception as e:
            logger.error(f"Database error: {e}")
    return None


def delete_care_task(db: Session, task_id: int, user_id: int) -> bool:
    """Delete a care task."""
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id,
        Plant.user_id == user_id
    ).first()
    if db_task:
        try:
            db.delete(db_task)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Database error: {e}")
    return False

def get_user_all_active_tasks(db: Session, user_id: int, limit: Optional[int] = None) -> List[PlantCareTask]:
    try:
        if limit:
            return db.query(PlantCareTask).filter(
                    PlantCareTask.user_id == user_id,
                    PlantCareTask.is_active == True
                ).order_by(PlantCareTask.due_date).limit(limit).all()

        return db.query(PlantCareTask).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.is_active == True
        ).order_by(PlantCareTask.due_date).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

# Read all plant care task of a specific plant for a user
def get_user_care_tasks_for_plant(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask]:
    """Get all tasks for a user of a specific plant."""
    try:
        return db.query(PlantCareTask).join(Plant).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.plant_id == plant_id,
            PlantCareTask.is_active == True).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

def get_tasks_by_date_for_plant(db: Session,
                                plant_id: int, user_id: int,
                                target_date: date) -> List[PlantCareTask]:
    """Get all tasks for a specific date for a user for a specific plant."""
    try:
        return db.query(PlantCareTask).join(Plant).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.plant_id == plant_id,
            PlantCareTask.due_date == target_date,
            PlantCareTask.is_active == True).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []


def get_all_delayed_tasks_for_plant(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask()]:
    """Get all delayed tasks of a specific plant for a user."""
    try:
        return db.query(PlantCareTask).join(Plant).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.plant_id == plant_id,
            PlantCareTask.due_date < date.today(),
            PlantCareTask.is_active == True).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

# Mark complete to a task
def complete_task(db: Session, task_id: int, user_id: int) -> bool:
    """Mark a task as completed and create completion history record."""
    # Get the task and verify ownership
    db_task = db.query(PlantCareTask).join(Plant).filter(
        PlantCareTask.id == task_id, Plant.user_id == user_id).first()
    if db_task:
        try:
            # Create completion history record
            completion_record = TaskCompletionHistory(plant_care_task_id=task_id)
            db.add(completion_record)
            # Update next due date if task is recurring
            if db_task.frequency_days > 0:
                db_task.due_date = date.today() + timedelta(days=db_task.frequency_days)
            db.commit()
            db.refresh(db_task)
            return True
        except Exception as e:
            db.refresh(db_task)
            logger.error(f"Database error: {e}")
    return False


# Read task completion history
def get_all_completed_tasks(db: Session, user_id: int) -> List[PlantCareTask]:
    """Get all tasks completed on a specific date."""
    try:
        return db.query(PlantCareTask).join(TaskCompletionHistory).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.id == TaskCompletionHistory.plant_care_task_id).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
    return []


def get_all_completed_tasks_of_plant(db: Session, plant_id: int, user_id: int) -> List[PlantCareTask]:
    """Get completion history for all tasks of a specific plant."""
    try:
        return db.query(
            PlantCareTask,
            TaskCompletionHistory.completed_at
        ).join(Plant).outerjoin(TaskCompletionHistory).filter(
            PlantCareTask.plant_id == plant_id,
            Plant.user_id == user_id
        ).order_by(TaskCompletionHistory.completed_at.desc()).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

def get_all_completed_tasks_by_date(db: Session, user_id: int, target_date: date) -> List[PlantCareTask]:
    """Get all tasks completed on a specific date."""
    try:
        return db.query(PlantCareTask).join(TaskCompletionHistory).filter(
            PlantCareTask.user_id == user_id,
            PlantCareTask.id == TaskCompletionHistory.plant_care_task_id,
            TaskCompletionHistory.completed_at == target_date, ).all()
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []
