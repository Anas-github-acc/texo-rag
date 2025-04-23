import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer 
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from tqdm import tqdm
import logging
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from fastapi import HTTPException
from convex import ConvexClient

load_dotenv('.env.local')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, collection_name: str = "rag_collection"):
        self.qdrant_url = os.getenv("QDRANT_API_URL")
        self.convex_url = os.getenv("CONVEX_URL")
        self.collection_name = collection_name
        self.model = SentenceTransformer("thenlper/gte-base", device="cpu")
        self.qdrant_api_key, self.gemini_api_key = self.load_environment()
        self.client = ConvexClient(self.convex_url)

    def load_environment(self):
        try:
            qdrant_api_key = os.getenv("QDRANT_API_KEY")
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not qdrant_api_key:
                raise ValueError("QDRANT_API_KEY not found in environment variables.")
            if not self.convex_url:
                raise ValueError("CONVEX_URL not found in environment variables.")
            return qdrant_api_key, gemini_api_key
        except Exception as e:
            logger.error(f"Failed to load environment variables: {e}")
            raise

    def clear_collection(self):
        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key, timeout=60.0)
            if client.collection_exists(collection_name=self.collection_name):
                client.delete_collection(collection_name=self.collection_name)
                logger.info(f"Deleted Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} does not exist")
        except Exception as e:
            logger.error(f"Failed to clear Qdrant collection: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to clear Qdrant collection: {str(e)}")

    def fetch_document_from_convex(self, document_id: str) -> dict:
        logger.info(f"Fetching document with ID {document_id} from Convex")
        # try:
        args = {"id": document_id}  # Changed from documentId to id
        document = self.client.query("documents:getById", args)
        print(f"Document fetched: {document}")
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        return document
        # except Exception as e:
        #     logger.error(f"Failed to fetch document {document_id}: {e}")
        #     raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
        if not text:
            logger.warning("Empty text provided for chunking")
            return []
        chunks = []
        start = 0
        text_length = len(text)
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            start += chunk_size - overlap
        logger.debug(f"Created {len(chunks)} chunks")
        return chunks

    def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        logger.info("Generating embeddings")
        if not chunks:
            logger.warning("No chunks provided for embedding")
            return []
        try:
            embeddings = self.model.encode(
                chunks, show_progress_bar=True, batch_size=16, normalize_embeddings=True
            )
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.WriteTimeout),
        before_sleep=lambda retry_state: logger.warning(f"Retrying due to timeout: attempt {retry_state.attempt_number}")
    )
    def upsert_with_retry(self, client, collection_name, points):
        client.upsert(collection_name=collection_name, points=points)

    def store_in_qdrant(self, embeddings: list[list[float]], chunks: list[str], source_map: list[str]):
        logger.info(f"Storing {len(embeddings)} points in Qdrant collection {self.collection_name}")
        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key, timeout=60.0)
            if not client.collection_exists(collection_name=self.collection_name):
                logger.info(f"Creating collection {self.collection_name}")
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=len(embeddings[0]) if embeddings else 768, distance=Distance.COSINE
                    )
                )
            batch_size = 100
            for i in tqdm(range(0, len(embeddings), batch_size), desc="Uploading batches"):
                batch_end = min(i + batch_size, len(embeddings))
                points = [
                    PointStruct(
                        id=i + j,
                        vector=embedding,
                        payload={"text": chunk, "source": source}
                    )
                    for j, (embedding, chunk, source) in enumerate(
                        zip(embeddings[i:batch_end], chunks[i:batch_end], source_map[i:batch_end])
                    )
                ]
                self.upsert_with_retry(client, self.collection_name, points)
            logger.info(f"Stored {len(embeddings)} points in Qdrant")
        except Exception as e:
            logger.error(f"Failed to store data in Qdrant: {e}")
            raise

    def search_similar_chunks(self, query: str, top_k: int = 3) -> list[dict]:
        logger.info(f"Searching for chunks similar to query: {query[:50]}...")
        try:
            query_embedding = self.model.encode(
                [query], show_progress_bar=False, normalize_embeddings=True
            ).tolist()[0]
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key, timeout=60.0)
            search_results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )
            results = [
                {
                    "text": result.payload.get("text", ""),
                    "source": result.payload.get("source", "unknown"),
                    "score": result.score
                }
                for result in search_results
            ]
            logger.info(f"Found {len(results)} similar chunks")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def generate_gemini_response(self, query: str, chunks: list[dict]) -> str:
        logger.info("Generating formal response with Gemini API")
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            context = "Relevant information from documents:\n"
            for i, chunk in enumerate(chunks, 1):
                context += f"Document {i} (Source: {chunk['source']}):\n{chunk['text']}\n\n"
            full_prompt = (
                f"Query: {query}\n\n"
                f"Using the information provided below, generate a clear, formal, and informative answer to the query.\n"
                f"If the answer can be found in the documents, respond based only on that.\n"
                f"If the documents do not contain sufficient or relevant information, mention that explicitly and provide a general answer.\n"
                f"---\n"
                f"Document Context:\n{context}\n"
                f"---"
            )
            response = model.generate_content(full_prompt)
            logger.info("Generated Gemini response")
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate Gemini response: {e}")
            raise

    def process_document(self, document_id: str):
        try:
            # For testing with hardcoded values, create a proper list of chunks
            document = self.fetch_document_from_convex(document_id)
            if not document or "initialContent" not in document:
                raise ValueError(f"Document with ID {document_id} not found or invalid format")
            
            text = document["initialContent"]
            if not text:
                raise ValueError("Document content is empty")
            
            all_chunks = self.chunk_text(text)
            if not all_chunks:
                raise ValueError("No chunks created from document content")
            
            source_map = ["test_source"] * len(all_chunks)  # Create matching source map
            
            logger.info(f"Prepared {len(all_chunks)} chunks from document {document_id}")
            embeddings = self.embed_chunks(all_chunks)
            
            if not embeddings or len(embeddings) == 0:
                raise ValueError("No embeddings generated")
                
            self.store_in_qdrant(embeddings, all_chunks, source_map)
            return {
                "status": "success", 
                "chunks": len(all_chunks), 
                "document_id": document_id
            }
        except Exception as e:
            logger.error(f"Process error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
