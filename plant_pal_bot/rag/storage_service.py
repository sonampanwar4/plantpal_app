"""
RAG Service for PlantPal - Hybrid Storage with ChromaDB + PostgreSQL
"""
from typing import Dict
from datetime import datetime
from datetime import timezone
from schemas.photo import DiagnosisResponse
import json
from models.plant import Plant
from logging import getLogger

logger = getLogger(__name__)

def create_document_text(diagnosis: DiagnosisResponse, plant_info: str) -> str:
    """
    Create rich text representation for embedding.
    Combines all relevant diagnosis information into searchable text.
    """
    # Main diagnosis text
    text_parts = [f"Diagnosis: {diagnosis.diagnosis_text}"]

    # Identified issues (from JSONB)
    if diagnosis.identified_issues:
        issues = json.dumps(diagnosis.identified_issues) if isinstance(diagnosis.identified_issues, dict) else str(
            diagnosis.identified_issues)
        issue_text = "Identified Issues:("
        for issue in issues:
            issue_text += ", " + issue
        text_parts.append(issue_text + ")")

    # Plant context (if available)
    if plant_info:
        text_parts.append(plant_info)

    # Treatment outcome (if available)
    if diagnosis.treatment_outcome:
        text_parts.append(f"Treatment Outcome: {diagnosis.treatment_outcome}")

    meta_text = " | ".join(text_parts)
    print(meta_text)
    return meta_text


def create_metadata(diagnosis: DiagnosisResponse, plant: Plant) -> Dict:
    """
    Create metadata for filtering and reference.
    This links back to PostgreSQL and enables filtered retrieval.
    """
    metadata = {
        "postgres_id": diagnosis.id,
        "photo_id": diagnosis.photo_id,
        "user_id": diagnosis.user_id,
        "recommended_actions": diagnosis.recommended_actions if isinstance(diagnosis.recommended_actions,
                                                                           dict) else str(
            diagnosis.recommended_actions),
        "confidence_score": float(diagnosis.confidence_score) if diagnosis.confidence_score else 0.0,
        "created_at": diagnosis.created_at.isoformat() if diagnosis.created_at else datetime.now(
            timezone.utc).isoformat(),
    }

    # Add treatment outcome if available
    if diagnosis.treatment_outcome:
        metadata["treatment_outcome"] = diagnosis.treatment_outcome

    # Add plant-specific metadata for filtering
    metadata["plant_species"] = plant.species if plant.species else plant.name

    return metadata
