import csv
import os
import uuid
from pinecone import Pinecone, Vector

bulk_index_threshold = 200
csv_file_path = 'vectors_100000.csv'
vector_db_name='pinecone'

api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)
index_name = 'test-vectors'
namespace = 'test_vectors'
client = pc.Index(index_name)

with open(csv_file_path, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file)
    vectors = []
    for i, row in enumerate(csv_reader):
        # ここで、CSVの各行からベクターを読み込む
        vector = [float(x) for x in row]  # CSVの行がベクターの数値データであると仮定
        vectors.append(Vector(id=str(uuid.uuid4()), values=vector))
        if len(vectors) >= bulk_index_threshold:
            # データをPineconeにアップロード
            client.upsert(vectors=vectors, namespace=namespace)
            vectors.clear()
            print(f'index to {vector_db_name} up to {i+1} row')

