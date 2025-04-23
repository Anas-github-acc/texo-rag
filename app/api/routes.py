import os
from fastapi import APIRouter, HTTPException, Depends
from app.api.pipeline import RAGPipeline
import logging
# from fastapi_clerk_auth import ClerkConfig, ClerkHTTPBearer, HTTPAuthorizationCredentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

router = APIRouter()

pipeline = RAGPipeline()

# Configure Clerk authentication
# clerk_config = ClerkConfig(jwks_url="https://example.com/.well-known/jwks.json") # Use your Clerk JWKS endpoint

# clerk_auth_guard = ClerkHTTPBearer(config=clerk_config)

@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    # user: HTTPAuthorizationCredentials | None = Depends(clerk_auth_guard),  # Use the configured auth instance
    # organization_id: str
):
    try:
        # Optionally, derive organization_id from user's Clerk profile if not provided
        # if not organization_id and user.organization_memberships:
        #     organization_id = user.organization_memberships[0].id
        result = pipeline.process_document(document_id)
        logger.info(f"Processed document {document_id} successfully")
        return result
    except Exception as e:
        logger.error(f"Process error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.get("/query")
async def query_similar_chunks(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    try:
        chunks = pipeline.search_similar_chunks(query)
        gemini_response = pipeline.generate_gemini_response(query, chunks)
        logger.info("Query processed successfully")
        return {"chunks": chunks, "gemini_response": gemini_response}
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")
