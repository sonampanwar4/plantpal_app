# Third-party imports
from sqlalchemy.orm import Session
from typing import Dict, Any

from plant_pal_bot.ai_bot_client import ask_gpt4o
from schemas.photo import ImageDiagnosisResponse, LocalPhotoDetail

from models.plant import Plant
from utils.chat_util import (
    format_similar_cases, generate_photo_diagnosis_summary,
    format_diagnosis_data
)
from services.plant_service import get_plant_service
from logging import getLogger
from utils.image_processor import validate_image_exists
from services.photo_service import (
    save_diagnosis_service, update_diagnosis_service,
    get_a_diagnosis_service, get_diagnoses_for_vector_db_service,
    save_plant_image_in_database_service, get_user_photo_by_id_service
)
from typing import Optional
# RAG implementation
from plant_pal_bot.rag.vector_embedding import vector_embedding

logger = getLogger(__name__)


class PlantPhotoAnalyze:
    def __init__(self,
                 db: Session,
                 user_query: str,
                 image_path: str,
                 user_id: int,
                 plant_id: int,
                 photo_id: Optional[int] = None,
                 local_photo_detail: Optional[LocalPhotoDetail] = None
                 ):
        self.user_id = user_id
        self.photo_id = photo_id
        self.user_query = user_query
        self.db = db
        self.image_path = image_path
        self.plant_id = plant_id
        self.local_photo_detail = local_photo_detail


    async def build_rag_context(self, plant: Plant) -> dict:
        """Get plant and all plant related photos details from the databases. """
        # ========== Fetch Plant Data ==========
        rag_context = {
            "plant": f"Plant type: {plant.name}, Species: {plant.species}, Location: {plant.plant_location}"
        }

        # ==== Find Similar Cases (RAG) for a specific plant to analyzing photo ===
        similar_cases_raw = await vector_embedding.find_similar_cases(
            user_query=self.user_query,
            plant_type=plant.name,
            k=3,
            confidence_threshold=0.7,
            successful_only=True
        )
        enriched = []
        # Fetch full details from PostgreSQL
        if similar_cases_raw:
            postgres_ids = [case["postgres_id"] for case in similar_cases_raw]
            full_diagnoses = get_diagnoses_for_vector_db_service(
                postgres_ids=postgres_ids,
                db=self.db
            )

            # Merge similarity scores with full data
            for raw_case in similar_cases_raw:
                matching_diagnosis = next(
                    (d for d in full_diagnoses if d.id == raw_case["postgres_id"]),
                    None
                )
                if matching_diagnosis:
                    enriched.append({
                        **raw_case,
                        "full_diagnosis": matching_diagnosis
                    })
            #TODO:
        rag_context["similar_cases"] = "".join(enriched) if enriched else ""
        return rag_context

    def build_diagnosis_prompt(self,
            plant_info: str,
            similar_cases_text: str) -> str:
        """Design prompt to analyzing photo with plant symptoms, details and historical similar cases """
        analysis_prompt = f"""Your task is to analyze plant image and provide detailed diagnostic information.

PLANT INFO: {plant_info}
USER CONCERN: {self.user_query}

SIMILAR CASES (maximum 3):
{similar_cases_text}
"""
        return analysis_prompt


    async def generate_rag_enhanced_diagnosis(self, user_prompt: str,) -> Dict[str, Any]:
        # ========== Call ChatGPT API (RAG) ==========
        ai_response = await ask_gpt4o(user_prompt=user_prompt,
                                      image_path=self.image_path,
                                      response_model=ImageDiagnosisResponse,
                                      temperature=0.3)  # more natural detailed reasoning

        return ai_response


    async def save_diagnosis(self, diagnosis: dict, plant: Plant) -> bool:
        """ Save or update diagnosis in PostgreSQL and index it in ChromaDB. """
        try:
            if not self.photo_id:
                photo = save_plant_image_in_database_service(db=self.db,
                                                             plant_id=self.plant_id,
                                                             user_id=self.user_id,
                                                             photo=self.local_photo_detail,
                                                             user_query=self.user_query
                                                             )
            else:
                photo = get_user_photo_by_id_service(db=self.db, photo_id=self.photo_id, user_id=self.user_id)
            if photo:
                exist_diagnosis = get_a_diagnosis_service(db=self.db, user_id=self.user_id, photo_id=photo.id)

                if not exist_diagnosis:
                    diagnosis_record = save_diagnosis_service(
                        db=self.db,
                        photo_id=photo.id,
                        user_id=photo.user_id,
                        diagnosis_data=diagnosis
                    )
                else:
                    diagnosis_record = update_diagnosis_service(
                        db=self.db,
                        diagnosis_id=exist_diagnosis.id,
                        user_id=photo.user_id,
                        update_data=diagnosis
                    )

                    # Delete old embedding in Chroma
                    if diagnosis_record:
                        deleted = vector_embedding.delete_from_chromadb(diagnosis_record.id)
                        if deleted:
                            logger.info(f"Deleted old diagnosis embedding from ChromaDB")


                if diagnosis_record:
                    try:
                        # Index the new/updated diagnosis in ChromaDB
                        success = await vector_embedding.index_diagnosis(diagnosis=diagnosis_record,
                                                                         plant=plant)
                        logger.info(f"Saved/updated diagnosis: {diagnosis_record}")
                        return success
                    except Exception as e:
                        logger.exception(f"Failed to save: {e}")
                return True
        except Exception as e:
            logger.exception(f"Failed to save diagnosis: {e}")
        return False

    async def get_llm_response(self) -> str | None:
        if not validate_image_exists(self.image_path):
            return "Sorry, this photo have not stored properly. Can you upload again?"

        plant = get_plant_service(db=self.db,
                                  plant_id=self.plant_id,
                                  user_id=self.user_id)

        try:
            # Extract plant and similar cases context
            rag_context = await self.build_rag_context(plant=plant)
            plant_info = rag_context["plant"]
            similar_cases = format_similar_cases(rag_context['similar_cases'])

            user_prompt = self.build_diagnosis_prompt(plant_info=plant_info, similar_cases_text=similar_cases)
            print(user_prompt)
            # Generate diagnosis data from LLM
            ai_response = await self.generate_rag_enhanced_diagnosis(user_prompt)
            if not ai_response:
                return None

            print(ai_response)

            if ai_response.get('is_plant_image'):
                diagnosis_data = ai_response.get('diagnosis', {})

                if diagnosis_data:
                    diagnosis = format_diagnosis_data(diagnosis_data)
                    await self.save_diagnosis(diagnosis=diagnosis,plant=plant)
                    final_response = generate_photo_diagnosis_summary(diagnosis, self.user_query)
                    return final_response

            else:
                return ai_response["error_message"]

        except Exception:
            raise
