import os
from locust import FastHttpUser, task, between, events
import numpy as np
from locust_util.locust_util import save_stats_csv

QUERY_VECTOR_SIZE = 1536
TOP_K = int(os.getenv("TOP_K", 10))
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NAMESPACE = "test_vectors"


class PineconeLoadTest(FastHttpUser):
    wait_time = between(0.5, 1)

    @task
    def search_test(self):
        query_vector = np.random.rand(QUERY_VECTOR_SIZE).tolist()
        payload = {
            "vector": query_vector,
            "topK": TOP_K,
            "includeValues": False,
            "includeMetadata": False,
            "namespace": NAMESPACE,
        }
        headers = {"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"}
        self.client.post(f"/query", headers=headers, json=payload)

@events.quitting.add_listener
def _(environment, **kw):
    filename = f"pinecone_top{TOP_K}"
    save_stats_csv(environment, filename)