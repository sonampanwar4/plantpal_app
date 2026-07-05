from fastapi import APIRouter
from plant_pal_bot.rag.vector_embedding import vector_embedding

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/rag")
async def check_rag_health():
    """Check if RAG system is working."""
    try:
        # Test ChromaDB connection
        collection = vector_embedding.vectorstore._collection
        count = collection.count()

        return {
            "status": "healthy",
            "chromadb_connected": True,
            "total_indexed_diagnoses": count,
            "message": "RAG system operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "chromadb_connected": False,
            "error": str(e)
        }
