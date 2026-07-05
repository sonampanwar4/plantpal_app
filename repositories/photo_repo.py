from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Optional, List, Dict, Any
from models.photo import PlantPhoto, PhotoDiagnosis
from schemas.photo import (
    PhotoCreate, PhotoDiagnosisCreate, PhotoDiagnosisUpdate,
    DiagnosisStatus, PhotoResponse
)
from datetime import datetime, timedelta, timezone
from models.plant import Plant
from logging import getLogger

logger = getLogger(__name__)


def create_photo(db: Session, photo_data: PhotoCreate) -> PhotoResponse | None:
    """Create a new photo record in database."""
    try:
        db_photo = PlantPhoto(**photo_data.model_dump())
        db.add(db_photo)
        db.commit()
        db.refresh(db_photo)
        return PhotoResponse.model_validate(db_photo)
    except Exception as e:
        logger.exception(f"💔Failed (create_photo) to database: {e}")
        return None


def get_photo_by_id(db: Session, photo_id: int, user_id: int) -> Optional[PlantPhoto] | None:
    """Get photo by ID for specific user."""
    try:
        return db.query(PlantPhoto).filter(
            and_(PlantPhoto.id == photo_id, PlantPhoto.user_id == user_id)
        ).first()
    except Exception as e:
        logger.error(f"Failed (get_photo_by_id) to database: {e}")
        return None

def get_user_image_by_file_path(db: Session, user_id: int, path: str) -> Optional[PlantPhoto] | None:
    """Get photo by ID for specific user."""
    try:
        return db.query(PlantPhoto).filter(
            and_(PlantPhoto.image_path == path, PlantPhoto.user_id == user_id)
        ).first()
    except Exception as e:
        logger.error(f"Failed (get_photo_by_id) to database: {e}")
        return None

def get_all_photos_related_a_plant(db: Session, plant_id: int, user_id: int):
    """Get all photo related of a specific plant by plant and user IDs for specific user."""
    try:
        return db.query(PlantPhoto).join(Plant).filter(
            Plant.id == plant_id,
            Plant.user_id == user_id).all()
    except Exception as e:
        logger.error(f"Failed (get_photo_by_id) to database: {e}")
        return None

def check_user_photo_exist(db: Session, user_id: int, plant_id: int, image_path: str) -> PhotoResponse | None:
    try:
        db_photo = db.query(PlantPhoto).filter(
            and_(PlantPhoto.image_path == image_path, PlantPhoto.user_id == user_id, PlantPhoto.plant_id == plant_id)
        ).first()
        return PhotoResponse.model_validate(db_photo)
    except Exception as e:
        logger.error(f"Failed (check_user_photo_exist) to database: {e}")
        return None

def get_user_photos(db: Session, user_id: int, limit: int = 50, offset: int = 0) -> List[PlantPhoto] | None:
    """Get all photos for a user with pagination."""
    try:
        return db.query(PlantPhoto).filter(
            PlantPhoto.user_id == user_id
        ).order_by(desc(PlantPhoto.created_at)).limit(limit).offset(offset).all()
    except Exception as e:
        logger.error(f"Failed (get_user_photos) to database: {e}")
        return None


def get_plant_photos(db: Session, plant_id: int, user_id: int) -> List[PlantPhoto()] | None:
    """Get all photos for a specific plant."""
    try:
        return db.query(PlantPhoto).filter(
            and_(PlantPhoto.plant_id == plant_id, PlantPhoto.user_id == user_id)
        ).order_by(desc(PlantPhoto.created_at)).all()
    except Exception as e:
        logger.error(f"Failed (get_plant_photos) to database: {e}")
        return None


def update_photo_status(db: Session, photo_id: int, status: str, user_id: int) -> Optional[
                                                                                                  PlantPhoto] | None:
    """Update photo diagnosis status."""
    try:
        photo = get_photo_by_id(db, photo_id, user_id)
        if photo:
            photo.diagnosis_status = status
            photo.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(photo)
        return photo
    except Exception as e:
        logger.error(f"Failed (update_photo_status) to database: {e}")
        return None


def delete_photo(db: Session, photo_id: int, user_id: int) -> bool:
    """Delete a photo and all related data."""
    try:
        photo = get_photo_by_id(db, photo_id, user_id)
        if photo:
            db.delete(photo)
            db.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Failed (delete_photo) to database: {e}")
        return False

# Diagnosis Repository Functions
def create_diagnosis(db: Session, diagnosis_data: PhotoDiagnosisCreate) -> PhotoDiagnosis | None:
    """Create a new diagnosis record."""
    try:
        db_diagnosis = PhotoDiagnosis(**diagnosis_data.model_dump())
        db.add(db_diagnosis)
        db.commit()
        db.refresh(db_diagnosis)
        return db_diagnosis
    except Exception as e:
        logger.exception(f"Failed (create_diagnosis) to database: {e}")
        raise


def get_diagnosis_by_photo_id(db: Session, photo_id: int, user_id: int) -> Optional[PhotoDiagnosis] | None:
    """Get the latest diagnosis for a photo."""
    try:
        return db.query(PhotoDiagnosis).filter(
            and_(PhotoDiagnosis.photo_id == photo_id, PhotoDiagnosis.user_id == user_id)
        ).order_by(desc(PhotoDiagnosis.created_at)).first()
    except Exception as e:
        logger.error(f"Failed (get_diagnosis_by_photo_id) to database: {e}")
        return None

def get_all_diagnosis_of_a_plant(db: Session, plant_id: int, user_id: int) -> List[PhotoDiagnosis()] | None:
    """Get all diagnoses of all plant photos for a specific plant."""
    try:
        diagnoses = (
            db.query(PhotoDiagnosis)
            .join(PlantPhoto, PhotoDiagnosis.photo_id == PlantPhoto.id)
            .join(Plant, PlantPhoto.plant_id == Plant.id)
            .filter(
                Plant.id == plant_id,
                Plant.user_id == user_id
            )
            .all()
        )
        return diagnoses
    except Exception as e:
        logger.exception(f"Failed (get_diagnoses_for_photo) to database: {e}")
        return None


def get_all_diagnoses_for_photo(db: Session, photo_id: int, user_id: int) -> List[PhotoDiagnosis()] | None:
    """Get all diagnoses for a photo (in case of re-analysis)."""
    try:
        return db.query(PhotoDiagnosis).filter(
            and_(PhotoDiagnosis.photo_id == photo_id, PhotoDiagnosis.user_id == user_id)
        ).order_by(desc(PhotoDiagnosis.created_at)).all()
    except Exception as e:
        logger.error(f"Failed (get_diagnoses_for_photo) to database: {e}")
        return None


def update_diagnosis(db: Session, diagnosis_id: int, update_data: PhotoDiagnosisUpdate, user_id: int) -> Optional[
                                                                                                        PhotoDiagnosis] | None:
    """Update an existing diagnosis."""
    try:
        diagnosis = db.query(PhotoDiagnosis).filter(
            and_(PhotoDiagnosis.id == diagnosis_id, PhotoDiagnosis.user_id == user_id)
        ).first()

        if diagnosis:
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(diagnosis, field, value)
            diagnosis.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(diagnosis)
        return diagnosis
    except Exception as e:
        logger.error(f"Failed (update_diagnosis) to database: {e}")
        return None


def get_user_diagnoses_history(db: Session, user_id: int, limit: int = 50) -> List[PhotoDiagnosis] | None:
    """Get user's diagnosis history for RAG context."""
    try:
        return db.query(PhotoDiagnosis).filter(
            PhotoDiagnosis.user_id == user_id
        ).order_by(desc(PhotoDiagnosis.created_at)).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed (get_user_diagnoses_history) to database: {e}")
        return None


def get_successful_diagnoses_for_rag(db: Session,
                                     plant_species: Optional[str] = None,
                                     limit: int = 10) -> List[PhotoDiagnosis()] | None:
    """Get successful diagnoses to use as RAG context."""
    try:
        query = db.query(PhotoDiagnosis).filter(PhotoDiagnosis.treatment_outcome.in_(["success", "cured", "improved"]))

        # If plant species is provided, try to filter by it
        if plant_species:
            # Join with photos and plants to filter by species
            query = query.join(PlantPhoto).join(Plant).filter(
                Plant.species.ilike(f"%{plant_species}%")
            )

        return query.order_by(desc(PhotoDiagnosis.confidence_score)).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed (get_successful_diagnoses_for_rag) to database: {e}")
        return None


# Analytics and Statistics Functions
def get_diagnosis_accuracy_stats(db: Session,
                                 user_id: Optional[int] = None,
                                 days: int = 30) -> Dict[str, Any] | None:
    """Get diagnosis accuracy statistics."""
    try:
        since_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(PhotoDiagnosis).filter(
            PhotoDiagnosis.created_at >= since_date
        )

        if user_id:
            query = query.filter(PhotoDiagnosis.user_id == user_id)

        total_diagnoses = query.count()
        successful_diagnoses = query.filter(
            PhotoDiagnosis.treatment_outcome.in_(["success", "cured", "improved"])
        ).count()

        avg_confidence = query.with_entities(
            func.avg(PhotoDiagnosis.confidence_score)
        ).scalar() or 0.0

        return {
            "total_diagnoses": total_diagnoses,
            "successful_diagnoses": successful_diagnoses,
            "success_rate": successful_diagnoses / total_diagnoses if total_diagnoses > 0 else 0.0,
            "average_confidence": float(avg_confidence),
            "period_days": days
        }
    except Exception as e:
        logger.error(f"Failed (get_diagnosis_accuracy_stats) to database: {e}")
        return None


def get_common_issues(db: Session,
                      user_id: Optional[int] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
    """Get most common plant issues from diagnoses."""
    query = db.query(PhotoDiagnosis)

    if user_id:
        query = query.filter(PhotoDiagnosis.user_id == user_id)

    diagnoses = query.filter(
        PhotoDiagnosis.identified_issues.is_not(None)
    ).all()

    # Count issues
    issue_counts = {}
    for diagnosis in diagnoses:
        if diagnosis.identified_issues:
            for category, issues in diagnosis.identified_issues.items():
                for issue in issues:
                    key = f"{category}: {issue}"
                    issue_counts[key] = issue_counts.get(key, 0) + 1

    # Sort by frequency and return top issues
    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    return [
        {"issue": issue, "count": count, "percentage": (count / len(diagnoses)) * 100}
        for issue, count in sorted_issues
    ]


def get_photos_needing_diagnosis(db: Session,
                                 user_id: Optional[int] = None) -> List[PlantPhoto()]:
    """Get photos that need diagnosis (pending or failed)."""
    query = db.query(PlantPhoto).filter(
        PlantPhoto.diagnosis_status.in_(
            [DiagnosisStatus.PENDING.value, DiagnosisStatus.FAILED.value])
    )

    if user_id:
        query = query.filter(PlantPhoto.user_id == user_id)

    return query.order_by(PlantPhoto.created_at).all()


def get_photos_with_diagnosis(db: Session,
                              user_id: int,
                              limit: int = 20) -> List[Dict[str, Any]]:
    """Get photos with their latest diagnosis for user dashboard."""
    photos = db.query(PlantPhoto).filter(
        PlantPhoto.user_id == user_id
    ).order_by(desc(PlantPhoto.created_at)).limit(limit).all()

    result = []
    for photo in photos:
        diagnosis = get_diagnosis_by_photo_id(db, photo.id, user_id)
        result.append({
            "photo": photo,
            "diagnosis": diagnosis,
            "has_diagnosis": diagnosis is not None
        })

    return result

def get_diagnoses_for_vector_db(db: Session,
                                postgres_ids: List[int]) -> List[PhotoDiagnosis()]:
    """Fetch full diagnosis records from PostgreSQL using IDs from ChromaDB."""
    try:

        diagnoses = db.query(PhotoDiagnosis).filter(
            PhotoDiagnosis.id.in_(postgres_ids)
        ).all()

        return diagnoses

    except Exception as e:
        print(f"Error fetching diagnosis details: {e}")
        return []