"""
Manages vector embeddings for PlantPal
"""
from typing import List, Dict, Optional
from langchain_chroma import Chroma  # still fine to keep
from logging import getLogger

from .storage_service import (
    create_document_text,
    create_metadata
)
from schemas.photo import DiagnosisResponse
from plant_pal_bot.ai_bot_client import get_embedding, get_embeddings
from langchain_core.embeddings import Embeddings
from models.plant import Plant
logger = getLogger(__name__)


class OpenAIEmbedding(Embeddings):
    """
    LangChain-compatible embeddings wrapper using OpenAI API directly.
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return get_embeddings(texts)

    def embed_query(self, text: str) -> List[float]:
        return get_embedding(text)


class ManageVectorEmbedding:
    """
    Manages vector embeddings in ChromaDB while keeping PostgreSQL as source of truth.
    """

    def __init__(self, persist_directory: str = "vector_db/chromadb"):
        """Initialize ChromaDB with OpenAI embeddings (no LangChain embeddings)."""

        self.embedding_function = OpenAIEmbedding()

        self.vectorstore = Chroma(
            collection_name="plant_diagnoses",
            embedding_function=self.embedding_function,
            persist_directory=persist_directory
        )

    async def index_diagnosis(
        self,
        diagnosis: DiagnosisResponse,
        plant: Plant
    ) -> bool:
        """
        Index a diagnosis in ChromaDB after it's saved to PostgreSQL.
        """
        plant_info = f"Plant Name: {plant.name} | Plant Type: {plant.species} | Plant location: {plant.plant_location}"
        try:
            doc_text = create_document_text(diagnosis, plant_info)
            logger.info(f"✅ ChromaDB document text: {doc_text}")

            metadata = create_metadata(diagnosis, plant)

            self.vectorstore.add_texts(
                texts=[doc_text],
                metadatas=[metadata],
                ids=[f"diagnosis_{diagnosis.id}"]
            )

            logger.info(f"✅ Background indexed diagnosis {diagnosis.id}")
            return True

        except Exception as e:
            logger.exception(f"Error indexing diagnosis {diagnosis.id}: {e}")
            return False

    async def find_similar_cases(
        self,
        user_query: str,
        plant_type: Optional[str] = None,
        k: int = 5,
        confidence_threshold: float = 0.7,
        successful_only: bool = True
    ) -> List[Dict]:
        """
        Find similar historical cases using semantic search.
        """
        try:
            filters = []

            if plant_type:
                filters.append({
                    "plant_species": {"$eq": plant_type}
                })

            if confidence_threshold > 0:
                filters.append({
                    "confidence_score": {"$gte": confidence_threshold}
                })

            if successful_only:
                filters.append({
                    "treatment_outcome": {
                        "$in": ["success", "resolved", "cured"]
                    }
                })

            results = self.vectorstore.similarity_search_with_score(
                query=user_query,
                k=k,
                filter={"$and": filters} if filters else None
            )

            similar_cases = []
            for doc, score in results:
                similar_cases.append({
                    "postgres_id": doc.metadata.get("postgres_id"),
                    "photo_id": doc.metadata.get("photo_id"),
                    "user_id": doc.metadata.get("user_id"),
                    "similarity_score": float(score),
                    "confidence_score": doc.metadata.get("confidence_score"),
                    "recommended_actions": doc.metadata.get("recommended_actions"),
                    "plant_species": doc.metadata.get("plant_species"),
                })

            return similar_cases

        except Exception as e:
            logger.exception(f"Error finding similar cases: {e}")
            return []

    def delete_from_chromadb(self, diagnosis_id: int) -> bool:
        """Delete a specific diagnosis from ChromaDB."""
        try:
            self.vectorstore.delete(ids=[f"diagnosis_{diagnosis_id}"])
            return True
        except Exception as e:
            logger.exception(f"⚠️ Error deleting from ChromaDB: {e}")
            return False



vector_embedding = ManageVectorEmbedding()
