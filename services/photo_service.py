from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from repositories.photo_repo import (
    create_photo, get_photo_by_id, update_photo_status, delete_photo,
    create_diagnosis, get_diagnosis_by_photo_id, update_diagnosis,
    get_user_photos, get_photos_with_diagnosis, get_photos_needing_diagnosis,
    get_successful_diagnoses_for_rag, get_user_diagnoses_history,
    check_user_photo_exist, get_all_diagnosis_of_a_plant,
    get_diagnoses_for_vector_db, get_user_image_by_file_path
)
from repositories.plant_repo import get_user_plant
from schemas.photo import (
    PhotoCreate, PhotoResponse, PhotoDiagnosisCreate, DiagnosisResponse,
    PhotoWithDiagnosis, DiagnosisStatus, PhotoDiagnosisUpdate, LocalPhotoDetail
)
from schemas.plant import PlantResponse
from utils.image_processor import (
    save_uploaded_image_on_local, delete_image_files, get_image_url, validate_image_exists
)
from models.photo import PlantPhoto, PhotoDiagnosis
from typing import Optional, Dict, List, Any, Tuple
from services.user_service import get_current_active_user_service
from plant_pal_bot.rag.vector_embedding import vector_embedding
from utils.image_processor import validate_image_file

from logging import getLogger

logger = getLogger(__name__)


async def save_user_photo_on_local_service(db: Session, file: UploadFile, user_id: int) -> LocalPhotoDetail:
    """
    Save and get user's plant photo.
    """
    try:
        # get current activate user
        user = get_current_active_user_service(user_id, db)
        # Save image file for the user on local machine
        photo_data = await save_uploaded_image_on_local(file, user)
        return photo_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


def save_plant_image_in_database_service(db: Session, photo: LocalPhotoDetail, user_id: int, plant_id: int, user_query: str):
    # Create photo record
    photo = PhotoCreate(
        user_id=user_id,
        plant_id=plant_id,
        image_path=photo.image_path,
        original_filename=photo.original_filename,
        file_size=photo.file_size,
        mime_type=photo.mime_type,
        user_query=user_query
    )
    return create_photo(db, photo)

def get_user_image_by_file_path_service(db: Session, user_id: int, photo_path: str):
    return get_user_image_by_file_path(db, user_id, photo_path)

def get_all_diagnosis_of_a_plant_service(db: Session, user_id: int, plant_id: int) -> List[PhotoDiagnosis()] | None:
    return get_all_diagnosis_of_a_plant(db=db, plant_id=plant_id, user_id=user_id)

def get_a_diagnosis_service(db: Session, user_id: int, photo_id: int) -> PhotoWithDiagnosis:
    """Get diagnosis by photo ID."""
    return get_diagnosis_by_photo_id(db, photo_id=photo_id, user_id=user_id)


def get_user_photo_by_id_service(db: Session, photo_id: int, user_id: int) -> Optional[PhotoResponse]:
    """Get photo by ID for specific user."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if photo:
        return PhotoResponse.model_validate(photo)
    return None

def get_user_photo_by_file_service(db, user_id: int, plant_id:int, photo_file) -> PlantResponse | None:
    if type(photo_file) is str:
        return check_user_photo_exist(db, user_id=user_id, plant_id=plant_id, image_path=photo_file)
    return None


def get_user_photos_with_diagnoses_service(db: Session, user_id: int, limit: int = 20) -> List[PhotoWithDiagnosis]:
    """Get user's photos with their diagnoses for dashboard."""
    photos_data = get_photos_with_diagnosis(db, user_id, limit)

    result = []
    for item in photos_data:
        photo = item['photo']
        diagnosis = item['diagnosis']

        # Get plant name if available
        plant_name = None
        if photo.plant_id:
            plant = get_user_plant(db, photo.plant_id, user_id)
            if plant:
                plant_name = plant.name

        photo_with_diagnosis = PhotoWithDiagnosis(
            photo=PhotoResponse.model_validate(photo),
            diagnosis=DiagnosisResponse.model_validate(diagnosis) if diagnosis else None,
            plant_name=plant_name
        )
        result.append(photo_with_diagnosis)
    return result


def get_user_diagnoses_history_service(db: Session, user_id: int, limit: int = 50) -> list:
    """Get user's diagnoses history for RAG context."""
    return get_user_diagnoses_history(db, user_id, limit)


def delete_user_photo_service(db: Session, photo_id: int, user_id: int) -> bool:
    """Delete a photo and its associated files."""
    db_photo = get_user_photo_by_id_service(db=db, user_id=user_id, photo_id=photo_id)
    if not db_photo:
        return False

    try:
        # Delete physical files
        if validate_image_exists(db_photo.image_path):
            delete_image_files(db_photo.image_path)

        # fetch diagnosis from database
        diagnosis = get_a_diagnosis_service(db=db, user_id=user_id, photo_id=db_photo.plant_id)
        # Delete database record (cascade will handle related records)
        success = delete_photo(db, db_photo.id, user_id)
        if success and diagnosis:
            # delete embedding from chromaDB
            deleted = vector_embedding.delete_from_chromadb(diagnosis.id)
            return deleted
        return success
    except Exception as e:
        logger.exception(f"Error deleting photo {db_photo.id}: {str(e)}")
        return False


def save_diagnosis_service(db: Session, photo_id: int, user_id: int,
                                   diagnosis_data: dict) -> DiagnosisResponse:
    """Create a diagnosis for a photo."""

    # Create diagnosis
    diagnosis = PhotoDiagnosisCreate(
        photo_id=photo_id,
        user_id=user_id,
        diagnosis_text=diagnosis_data['diagnosis_text'],
        identified_issues=diagnosis_data['identified_issues'],
        recommended_actions=diagnosis_data['recommended_actions'],
        confidence_score=diagnosis_data['confidence_score'],
        treatment_outcome=diagnosis_data['treatment_outcome']
    )

    diagnosis = create_diagnosis(db, diagnosis)
    if diagnosis is None:
        raise RuntimeError("Diagnosis creation failed; see logs for details")

    # Update photo status to analyzed
    update_photo_status(db, photo_id, DiagnosisStatus.ANALYZED.value, user_id)

    return DiagnosisResponse.model_validate(diagnosis)


def get_latest_photo_diagnosis_service(db: Session, photo_id: int, user_id: int) -> Optional[DiagnosisResponse]:
    """Get the latest diagnosis for a photo."""
    diagnosis = get_diagnosis_by_photo_id(db, photo_id, user_id)
    if diagnosis:
        return DiagnosisResponse.model_validate(diagnosis)
    return None


def update_diagnosis_service(db: Session, diagnosis_id: int, user_id: int,
                                   update_data: dict) -> DiagnosisResponse | None:
    """Update an existing diagnosis."""
    try:
        diagnosis = PhotoDiagnosisUpdate(
            diagnosis_text=update_data['diagnosis_text'],
            identified_issues=update_data['identified_issues'],
            recommended_actions=update_data['recommended_actions'],
            confidence_score=update_data['confidence_score'],
            treatment_outcome=update_data["treatment_outcome"]
        )
        update_diagnosis_data = update_diagnosis(db, diagnosis_id, diagnosis, user_id)
        return DiagnosisResponse.model_validate(update_diagnosis_data)
    except Exception:
        return None


def get_photo_url_for_display_service(photo: PhotoResponse, thumbnail: bool = False) -> str:
    """Get URL for displaying photo in frontend."""
    return get_image_url(photo.image_path, thumbnail=thumbnail)


def get_photos_needing_analysis_service(db: Session, user_id: Optional[int] = None) -> List[PhotoResponse]:
    """Get photos that need diagnosis."""
    photos = get_photos_needing_diagnosis(db, user_id)
    return [PhotoResponse.model_validate(photo) for photo in photos]


def prepare_photo_for_analysis_service(db: Session, photo_id: int, user_id: int) -> Dict[str, Any]:
    """Prepare photo data for AI analysis."""
    photo = get_photo_by_id(db, photo_id, user_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Update status to analyzing
    update_photo_status(db, photo_id, DiagnosisStatus.ANALYZED.value, user_id)

    # Prepare data for analysis
    analysis_data = {
        'photo_id': photo.id,
        'user_id': user_id,
        'image_path': photo.image_path,
        'upload_context': photo.user_query,
        'plant_id': photo.plant_id,
        'original_filename': photo.original_filename,
        'created_at': photo.created_at.isoformat()
    }

    # Add plant context if available
    if photo.plant_id:
        plant = get_user_plant(db, photo.plant_id, user_id)
        if plant:
            analysis_data['plant_context'] = {
                'name': plant.name,
                'species': plant.species,
                'location': plant.location,
                'current_issues': plant.notes
            }

    return analysis_data


def handle_analysis_failure_service(db: Session, photo_id: int, user_id: int, error_message: str) -> None:
    """Handle failed photo analysis."""
    # Update photo status to failed
    update_photo_status(db, photo_id, DiagnosisStatus.FAILED, user_id)

    # Create a diagnosis record with the error
    try:
        diagnosis_data = PhotoDiagnosisCreate(
            photo_id=photo_id,
            user_id=user_id,
            diagnosis_text=f"Analysis failed: {error_message}",
            confidence_score=0.0,
            identified_issues={"errors": ["analysis_failed"]},
            recommended_actions={"immediate": ["retry_analysis", "contact_support"]},
            treatment_outcome= "failed"
        )
        create_diagnosis(db, diagnosis_data)
    except Exception as e:
        logger.error(f"Failed to create error diagnosis for photo {photo_id}: {str(e)}")


def get_analysis_statistics_service(db: Session, user_id: int) -> Dict[str, Any]:
    """Get photo analysis statistics for user."""
    from repositories.photo_repo import get_diagnosis_accuracy_stats, get_common_issues

    # Get accuracy stats
    stats = get_diagnosis_accuracy_stats(db, user_id, days=30)

    # Get common issues
    common_issues = get_common_issues(db, user_id, limit=5)

    # Get photo counts by status
    user_photos = get_user_photos(db, user_id, limit=1000)  # Get all for counting
    status_counts = {}
    for photo in user_photos:
        status = photo.diagnosis_status
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        'accuracy_stats': stats,
        'common_issues': common_issues,
        'photo_counts_by_status': status_counts,
        'total_photos': len(user_photos)
    }


def validate_photo_for_chat_service(db: Session, photo_id: int, user_id: int) -> Tuple[
    bool, Optional[str], Optional[PlantPhoto]]:
    """
    Validate photo for analyse_chat_2 integration.

    Returns:
        Tuple of (is_valid, error_message, photo_object)
    """
    photo = get_photo_by_id(db, photo_id, user_id)

    if not photo:
        return False, "Photo not found", None

    if not validate_image_exists(photo.image_path):
        return False, "Image file not found", None

    return True, None, photo


def get_photo_context_for_chat_service(photo: PhotoResponse, db: Session) -> Dict[str, Any]:
    """Get photo context for analyse_chat_2 AI analysis."""
    context = {
        'photo_id': photo.id,
        'upload_context': photo.user_query,
        'diagnosis_status': photo.diagnosis_status,
        'created_at': photo.created_at.isoformat(),
        'file_info': {
            'original_filename': photo.original_filename,
            'file_size': photo.file_size,
            'mime_type': photo.mime_type
        }
    }

    # Add plant context if available
    plant = get_user_plant(db, photo.plant_id, photo.user_id)
    if plant:
        context['plant'] = {
            'name': plant.name,
            'species': plant.species,
            'location': plant.location,
            'notes': plant.notes
        }

    # Add existing diagnosis if available
    existing_diagnosis = get_diagnosis_by_photo_id(db, photo.id, photo.user_id)
    if existing_diagnosis:
        context['existing_diagnosis'] = {
            'diagnosis_text': existing_diagnosis.diagnosis_text,
            'confidence_score': existing_diagnosis.confidence_score,
            'identified_issues': existing_diagnosis.identified_issues,
            'similar_cases': existing_diagnosis.similar_cases_used,
            'recommended_actions': existing_diagnosis.recommended_actions,
            'created_at': existing_diagnosis.created_at.isoformat()
        }

    return context


def get_successful_diagnoses_for_rag_service(db: Session, plant_species: Optional[str] = None, limit: int = 50) -> list:
    """Get successful diagnoses to use as RAG context."""
    return get_successful_diagnoses_for_rag(db, plant_species=plant_species, limit=limit)


def get_diagnoses_for_vector_db_service(db, postgres_ids: List[int]):
    """Fetch full diagnosis records from PostgreSQL using IDs from ChromaDB."""
    return get_diagnoses_for_vector_db(db=db, postgres_ids=postgres_ids)