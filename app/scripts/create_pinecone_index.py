from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)

pc.create_index(
    name="ticket-resolutions",
    dimension=1536,
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
)

print("Pinecone index created successfully.")
