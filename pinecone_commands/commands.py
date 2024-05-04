import os
import time
from pinecone import Pinecone, Vector

api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)
index_name = 'test-index'
namespace = 'test_vectors'
client = pc.Index(index_name)

def upsert_vectors(vectors):
    pVectors = [
        Vector(id=str(vector["id"]), values=vector["vector"])
        for vector in vectors
    ]
    start = time.time()
    client.upsert(vectors=pVectors, namespace=namespace)
    end = time.time()
    took_time = end-start
    print(f'index to pinecone up to {pVectors[-1].id} row took {took_time} seconds')
    return {"task_name": f"upsert_pinecone_{index_name}_{namespace}", "took_time": took_time}