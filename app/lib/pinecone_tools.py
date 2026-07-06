from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.core.config import settings

embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index("ticket-resolutions")
vector_store = PineconeVectorStore(index=index, embedding=embeddings)


def search_similar_tickets(description: str, category: str, k: int = 3) -> str:
    """
    Searches Pinecone for similar past resolved tickets in the same category.
    Returns formatted context string for use in agent prompts.
    """

    try:
        results = vector_store.similarity_search(
            description, k=k, filter={"category": category}
        )
        if not results:
            return "No similar past tickets found."

        context_parts = []
        for i, doc in enumerate(results, 1):
            resolution = doc.metadata.get("resolution", "No resolution recorded")
            context_parts.append(
                f"{i}. {doc.page_content}\n   Resolution: {resolution}"
            )

            return "\n".join(context_parts)
    except Exception:
        return "No similar past tickets found."


def store_resolved_ticket(description: str, resolution: str, category: str) -> None:
    """
    Stores a resolved ticket in Pinecone so future agents can find it.
    """
    vector_store.add_texts(
        texts=[description],
        metadatas=[{"resolution": resolution, "category": category}],
    )
