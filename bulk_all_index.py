import argparse

import concurrent.futures
import time

import numpy as np

from pinecone_commands.commands import upsert_vectors
from qdrant.commands import update_index_threshold, upsert_points


def bulk_index_by_random_vector(
    collection_name, index_number, bulk_index_threshold, parallel_count=1
):
    print(
        f"bulk_index_by_random_vector: index_number={index_number}, bulk_index_threshold={bulk_index_threshold}, parallel_count={parallel_count}"
    )
    start_time = time.time()
    # 一時的にindexをdisableする
    update_index_threshold(collection_name, 0)

    task_took_time = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
        futures = []
        crate_vector_start_time = time.time()
        print(f"start vector generation")
        vectors = [
            {"id": i + 1, "vector": np.random.rand(1536).tolist()}
            for i in range(index_number)
        ]
        print(f"end vector generation took {time.time() - crate_vector_start_time} seconds")
        chunk_vector_start_time = time.time()
        print(f"start chunk vector")
        chunked_vectors = [
            vectors[i : i + bulk_index_threshold]
            for i in range(0, index_number, bulk_index_threshold)
        ]
        print(f"end chunk vector took {time.time() - chunk_vector_start_time} seconds")
        for vectors in chunked_vectors:
            futureQdrant = executor.submit(upsert_points, vectors, collection_name)
            futurePincone = executor.submit(upsert_vectors, vectors)
            futures.append(futureQdrant)
            futures.append(futurePincone)

        # Wait for all the futures to complete and handle results
        for res in concurrent.futures.as_completed(futures):
            if res.exception():
                print(f"Exception: {res.exception()}")
            else:
                task_result = res.result()
                if task_result["task_name"] in task_took_time:
                    task_took_time[task_result["task_name"]] += task_result["took_time"]
                else:
                    task_took_time[task_result["task_name"]] = task_result["took_time"]

    # indexを有効化する
    update_index_threshold(collection_name, 20000)

    end_time = time.time()
    print(f"====took time====")
    for task_name, took_time in task_took_time.items():
        print(f"{task_name} took {took_time} seconds")
    print(f"total took {end_time - start_time} seconds")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    bulk_index_parser = subparsers.add_parser("bulk_index")
    bulk_index_parser.add_argument(
        "--q_collection_name",
        type=str,
        default="test_vectors",
        help="Name of Qdrant Collection name",
    )
    bulk_index_parser.add_argument(
        "--index_num",
        type=int,
        default=10000,
        help="Number of vectors to index",
    )
    bulk_index_parser.add_argument(
        "--index_threshold",
        type=int,
        default=200,
        help="Threshold for bulk indexing",
    )
    bulk_index_parser.add_argument(
        "--parallel_count",
        type=int,
        default=2,
        help="Number of parallel indexing",
    )
    bulk_index_parser.set_defaults(
        func=lambda args: bulk_index_by_random_vector(
            args.q_collection_name,
            args.index_num,
            args.index_threshold,
            args.parallel_count,
        )
    )

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
