import os
import logging
from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

logger = logging.getLogger(__name__)

class VectorStoreService:
    _qdrant_store = None

    @classmethod
    async def get_qdrant_store(cls):
        """
        Singleton pattern to get the Qdrant Vector Store instance.
        """
        if cls._qdrant_store:
            return cls._qdrant_store

        if not os.getenv("QUADRANT_CLUSTER_ENDPOINT"):
            return None

        try:
            url = os.getenv("QUADRANT_CLUSTER_ENDPOINT")
            api_key = os.getenv("QUADRANT_CLUSTER_API_KEY")
            
            # Initialize Client explicitly
            client = QdrantClient(url=url, api_key=api_key)
            
            collection_name = os.getenv("QDRANT_COLLECTION_NAME")
            
            # Check if collection exists
            if not client.collection_exists(collection_name):
                try:
                    logger.info(f"Creating Qdrant collection: {collection_name}")
                    client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=768, 
                            distance=Distance.COSINE,
                            on_disk=False
                        ),
                    )
                    # 1. Create the Tenant index (Partitioning)
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="user_id",
                        field_schema="keyword"
                    )

                    # 2. Create the Thread index (Faster filtering for chat history)
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="thread_id",
                        field_schema="keyword"
                    )
                except Exception as e:
                    logger.error(f"Failed to create collection: {e}")

            # Connect: Now it is safe to use 'from_existing_collection'
            embeddings = OllamaEmbeddings(model="nomic-embed-text")
            cls._qdrant_store = QdrantVectorStore.from_existing_collection(
                embedding=embeddings,
                collection_name=collection_name,
                url=url,
                api_key=api_key,
            )
            return cls._qdrant_store
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant Store: {e}")
            return None

    @classmethod
    async def delete_thread_vectors(cls, thread_id: str) -> bool:
        """
        Deletes all vector points associated with a specific thread_id.
        Returns True on success, False if an error occurred.
        """
        try:
            store = await cls.get_qdrant_store()
            if not store:
                logger.warning("Could not delete vectors: Qdrant store not available")
                return False

            collection_name = os.getenv("QDRANT_COLLECTION_NAME")
            if not collection_name:
                logger.warning("Could not delete vectors: QDRANT_COLLECTION_NAME not set")
                return False

            from qdrant_client.http import models

            # Use the underlying client to perform a deletion by filter
            store.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="thread_id",
                                match=models.MatchValue(value=thread_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Successfully deleted Qdrant vectors for thread: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Qdrant vectors for thread {thread_id}: {e}")
            return False
