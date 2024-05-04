import os
import numpy as np
from pinecone import Pinecone, Vector
import time

api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)
index_name = 'test-vectors'
namespace='test_vectors'
client = pc.Index(index_name)
top_k=10
include_values=False
include_metadata=False


# ランダムなベクトルの生成
dimensions = 1536
vector = np.random.rand(dimensions).tolist()

start_time = time.time()
response = client.query(
    namespace=namespace,
    vector=vector,
    top_k=top_k,
    include_values=include_values,
    include_metadata=include_metadata,
)
end_time = time.time()

# 応答時間の計算
response_time = end_time - start_time
print(f"Response time: {response_time} seconds")
print(response)