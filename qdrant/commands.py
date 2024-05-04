import os
import numpy as np
import time
import csv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
import time

# Qdrantクライアントの初期化
# local
client = QdrantClient(host="localhost", port=6333)
if os.getenv("QDRANT_HOST") and os.getenv("QDRANT_API_KEY"):
    client = QdrantClient(
        url=os.getenv("QDRANT_HOST"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )


def get_collection_info(collection_name):
    # コレクションの情報を取得
    collection_info = client.get_collection(collection_name=collection_name)
    return collection_info


def create_collection(
    collection_name: str,
    vector_size: int,
    on_disk: bool,
    shard_number: int,
    replica_number: int,
    max_segment_size: int | None,
):
    optimzers_config = models.OptimizersConfigDiff()
    if max_segment_size is not None:
        optimzers_config.max_segment_size = max_segment_size
    # optimzers_config.default_segment_number = 8
    # コレクションの作成
    client.create_collection(
        collection_name=collection_name,
        shard_number=shard_number,
        replication_factor=replica_number,
        vectors_config=models.VectorParams(
            size=vector_size, distance=models.Distance.COSINE, on_disk=on_disk
        ),
        optimizers_config=optimzers_config,
        quantization_config=models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8, quantile=0.99, always_ram=True
            )
        ),
    )
    print(
        f"Collection '{collection_name}' shard_number={shard_number} created successfully."
    )


def import_collection_by_file(collection_name: str, file_path: str):
    client.upload_collection(collection_name=collection_name, location=file_path)


def search(collection_name, top_k, query_vector_size):
    query_vector = np.random.rand(query_vector_size).tolist()
    # 検索の実行と応答時間の計測
    start_time = time.time()
    response = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=None,
        limit=top_k,
        offset=0,
    )
    end_time = time.time()

    # 応答時間の計算
    response_time = end_time - start_time

    return response, response_time


def update_index_threshold(collection_name, threshold):
    start = time.time()
    client.update_collection(
        collection_name=collection_name,
        optimizer_config=models.OptimizersConfigDiff(indexing_threshold=threshold),
    )
    end = time.time()
    print(f"update qdrant index threshold to {threshold}kb took {end-start} seconds")


def bulk_index_from_csv(collection_name, csv_file_path, bulk_index_threshold):
    start_time = time.time()
    # 一時的にindexをdisableする
    update_index_threshold(collection_name, 0)

    with open(csv_file_path, mode="r") as csv_file:
        csv_reader = csv.reader(csv_file)
        points = []
        for i, row in enumerate(csv_reader):
            # ここで、CSVの各行からベクターを読み込む
            vector = [
                float(x) for x in row
            ]  # CSVの行がベクターの数値データであると仮定
            point = PointStruct(id=i, vector=vector, payload={})
            points.append(point)

            if len(points) >= bulk_index_threshold:
                retry_count = 0
                while retry_count < 3:
                    try:
                        start = time.time()
                        client.upsert(points=points, collection_name=collection_name)
                        end = time.time()
                        points.clear()
                        print(
                            f"index to qdrant up to {i+1} row took {end-start} seconds"
                        )
                        break
                    except Exception as e:
                        print(f"Upsert failed: {e}")
                        retry_count += 1
                        time.sleep(1)  # Wait for 1 second before retrying
                        if retry_count == 3:
                            print("Upsert failed after 3 retries, so exit")
                            raise e
            if len(points) >= bulk_index_threshold:
                client.upsert(points=points, collection_name=collection_name)
                points.clear()
                print(f"index to qdrant up to {i+1} row")

    # indexを有効化する
    update_index_threshold(collection_name, 20000)

    return time.time() - start_time


def delete_collection(collection_name):
    # コレクションの削除
    client.delete_collection(collection_name=collection_name)
    print(f"Collection '{collection_name}' deleted successfully.")


import concurrent.futures


def upsert_points(vectors, collection_name):
    points = [
        PointStruct(id=vector["id"], vector=vector["vector"], payload={})
        for vector in vectors
    ]
    retry_count = 0
    while retry_count < 3:
        try:
            start = time.time()
            client.upsert(points=points, collection_name=collection_name)
            end = time.time()
            took_time = end - start
            print(f"index to qdrant up to {points[-1].id} row took {took_time} seconds")
            return {
                "task_name": f"upsert_qdrant_{collection_name}",
                "took_time": took_time,
            }
        except Exception as e:
            print(f"Upsert failed: {e}")
            retry_count += 1
            time.sleep(1)  # Wait for 1 second before retrying
            if retry_count == 3:
                print("Upsert failed after 3 retries, so exit")
                raise e


def bulk_index_by_random_vector(
    collection_name, vector_size, index_number, bulk_index_threshold, parallel_count=1
) -> float:
    start_time = time.time()
    # 一時的にindexをdisableする
    update_index_threshold(collection_name, 0)

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
        futures = []
        for i in range(0, index_number, bulk_index_threshold):
            vectors = vectors = [
                {"id": j + 1, "vector": np.random.rand(vector_size).tolist()}
                for j in range(i, i + bulk_index_threshold)
            ]
            future = executor.submit(upsert_points, vectors, collection_name)
            futures.append(future)

        # Wait for all the futures to complete
        concurrent.futures.wait(futures)

    # indexを有効化する
    update_index_threshold(collection_name, 20000)

    end_time = time.time()
    took_time = end_time - start_time
    print(f"bulk_index_by_random_vector took {took_time} seconds")
    return took_time


def wait_for_green_status(collection_name, max_wait_time) -> float:
    start_time = time.time()
    green_count = 0
    while green_count < 30:
        collection_info = get_collection_info(collection_name)
        status = collection_info.status
        if status == "green":
            green_count += 1
            print(
                f"Collection status is green. Ready to proceed. green_count={green_count}"
            )
        else:
            green_count = 0
        # if time.time() - start_time >= max_wait_time:
        #     print("Max wait time exceeded. Exiting.")
        #     break
        time.sleep(1)
    return time.time() - start_time
