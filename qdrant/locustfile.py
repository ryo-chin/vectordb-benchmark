from locust import FastHttpUser, task, between, events
import numpy as np
import os

from locust_util.locust_util import save_stats_csv

QUERY_VECTOR_SIZE = 1536
TOP_K = int(os.getenv("TOP_K", 10))
COLLECTION_NAME = "test_vectors"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


class QdrantLoadTest(FastHttpUser):
    wait_time = between(0.5, 1)

    @task
    def search_test(self):
        query_vector = np.random.rand(QUERY_VECTOR_SIZE).tolist()
        payload = {"vector": query_vector, "limit": TOP_K}
        headers = {"Api-Key": QDRANT_API_KEY, "Content-Type": "application/json"}
        self.client.post(
            f"/collections/{COLLECTION_NAME}/points/search",
            json=payload,
            headers=headers,
        )

@events.quitting.add_listener
def _(environment, **kw):
    filename = f"qdrant_top{TOP_K}"
    save_stats_csv(environment, filename)