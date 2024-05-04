import argparse
from dataclasses import dataclass
import datetime

from pydantic import BaseModel
from qdrant.commands import (
    bulk_index_by_random_vector,
    create_collection,
    delete_collection,
    get_collection_info,
    search,
    bulk_index_from_csv,
    wait_for_green_status,
)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


@dataclass
class CreateCollectionParams:
    collection_name: str
    vector_size: int
    on_disk: bool
    shard_number: int
    replica_number: int
    max_segment_size: int | None


def create_collection_function(params: CreateCollectionParams):
    print(f"on_disk: {params.on_disk}")
    create_collection(
        params.collection_name,
        params.vector_size,
        params.on_disk,
        params.shard_number,
        params.replica_number,
        params.max_segment_size,
    )


@dataclass
class BulkIndexParams:
    collection_name: str
    csv_file_path: str
    vector_size: int
    index_threshold: int
    index_num: int
    parallel_count: int
    wait_cluster_ready: bool
    interval: int = 5
    timeout: int = 600


class BulkIndexResult(BaseModel):
    index_took_time: float
    index_completed_time: datetime.datetime
    optimize_took_time: float
    optimize_completed_time: datetime.datetime


def bulk_index_function(params: BulkIndexParams):
    index_took_time = 0
    if params.csv_file_path is None:
        index_took_time = bulk_index_by_random_vector(
            params.collection_name,
            params.vector_size,
            params.index_num,
            params.index_threshold,
            params.parallel_count,
        )
    else:
        index_took_time = bulk_index_from_csv(
            params.collection_name, params.csv_file_path, params.index_threshold
        )
    index_completed_time = datetime.datetime.now()
    optimezed_time = 0
    if params.wait_cluster_ready:
        optimezed_time = wait_for_green_status(
            params.collection_name, params.timeout
        )
    optimeze_completed_time = datetime.datetime.now()

    bulk_index_result = BulkIndexResult(
        index_took_time=index_took_time,
        index_completed_time=index_completed_time,
        optimize_took_time=optimezed_time,
        optimize_completed_time=optimeze_completed_time,
    )
    print(bulk_index_result.model_dump_json(indent=4))


def search_function(collection_name, top_k, query_vector_size, output_response):
    [res, response_time] = search(collection_name, top_k, query_vector_size)
    print(f"Response time: {response_time} seconds")
    print(f"Top k: {top_k}")
    print(f"Collection name: {collection_name}")
    print(f"Query vector size: {query_vector_size}")
    if output_response:
        print(res)


def delete_collection_functions(collection_name):
    delete_collection(collection_name)


def info_function(collection_name):
    collection_info = get_collection_info(collection_name)
    print(collection_info.model_dump_json(indent=4))


@dataclass
class RecreateCollectionParams:
    collection_name: str
    create_collection_params: CreateCollectionParams
    bulk_index_params: BulkIndexParams


def recreate_function(params: RecreateCollectionParams):
    delete_collection(params.collection_name)
    create_collection_function(params.create_collection_params)
    bulk_index_function(params.bulk_index_params)
    info_function(params.collection_name)


DEFAULT_COLLECTION_NAME = "test_vectors"
DEFAULT_VECTOR_SIZE = 1536


def setup_create_collection_parser(subparsers, create_collection_command):
    create_collection_parser = subparsers.add_parser(create_collection_command)

    create_collection_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    setup_create_collection_args(create_collection_parser)
    create_collection_parser.set_defaults(
        func=lambda args: create_collection_function(toCreateCollectionParams(args))
    )


def toCreateCollectionParams(args):
    return CreateCollectionParams(
        collection_name=args.collection_name,
        vector_size=args.vector_size,
        on_disk=args.on_disk,
        shard_number=args.shard_number,
        replica_number=args.replica_number,
        max_segment_size=args.max_segment_size,
    )


def setup_create_collection_args(create_collection_parser):
    create_collection_parser.add_argument(
        "--vector_size", type=int, default=DEFAULT_VECTOR_SIZE, help="Vector size"
    )
    create_collection_parser.add_argument(
        "--on_disk", type=str2bool, default=True, help="Store vectors on disk"
    )
    create_collection_parser.add_argument(
        "--shard_number", type=int, default=2, help="Number of shards"
    )
    create_collection_parser.add_argument(
        "--replica_number", type=int, default=2, help="Number of replicas"
    )
    create_collection_parser.add_argument(
        "--max_segment_size", type=int, default=None, help="Max segment size"
    )


def setup_bulk_index_parser(subparsers, bulk_index_command):
    bulk_index_parser = subparsers.add_parser(bulk_index_command)
    bulk_index_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    setup_bulk_index_args(bulk_index_parser)
    bulk_index_parser.set_defaults(
        func=lambda args: bulk_index_function(toBulkIndexParams(args))
    )


def toBulkIndexParams(args):
    return BulkIndexParams(
        collection_name=args.collection_name,
        csv_file_path=args.csv_file_path,
        vector_size=args.vector_size,
        index_threshold=args.index_threshold,
        index_num=args.index_num,
        parallel_count=args.parallel_count,
        wait_cluster_ready=args.wait_cluster_ready,
        interval=args.interval,
        timeout=args.timeout,
    )


def setup_bulk_index_args(bulk_index_parser):
    bulk_index_parser.add_argument(
        "--csv_file_path",
        type=str,
        help="Path to the CSV file",
    )
    bulk_index_parser.add_argument(
        "--vector_size", type=int, default=DEFAULT_VECTOR_SIZE, help="Vector size"
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
    bulk_index_parser.add_argument(
        "--wait_cluster_ready",
        type=str2bool,
        default=True,
        help="Wait for cluster to be ready",
    )
    bulk_index_parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Interval to check cluster status",
    )
    bulk_index_parser.add_argument(
        "--timeout",
        type=int,
        default=3600*10,
        help="Timeout to check cluster status",
    )


def setup_search_parser(subparsers, search_command):
    search_parser = subparsers.add_parser(search_command)
    search_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    search_parser.add_argument(
        "--top_k", type=int, default=10, help="Number of results to retrieve"
    )
    search_parser.add_argument(
        "--output_response", type=bool, default=False, help="Output response or not"
    )
    search_parser.add_argument(
        "--query-vector-size", type=int, default=DEFAULT_VECTOR_SIZE, help="Vector size"
    )
    search_parser.set_defaults(
        func=lambda args: search_function(
            args.collection_name,
            args.top_k,
            args.query_vector_size,
            args.output_response,
        )
    )


def setup_delete_collection_parser(subparsers, delete_collection_command):
    delete_collection_parser = subparsers.add_parser(delete_collection_command)
    delete_collection_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    delete_collection_parser.set_defaults(
        func=lambda args: delete_collection_functions(args.collection_name)
    )


def setup_info_parser(subparsers, info_command):
    info_parser = subparsers.add_parser(info_command)
    info_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    info_parser.set_defaults(func=lambda args: info_function(args.collection_name))


def setup_recreate_collection_parser(subparsers, recreate_command):
    recreate_parser = subparsers.add_parser(recreate_command)
    recreate_parser.add_argument(
        "--collection_name",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help="Collection name",
    )
    setup_create_collection_args(recreate_parser)
    setup_bulk_index_args(recreate_parser)
    recreate_parser.set_defaults(
        func=lambda args: recreate_function(
            RecreateCollectionParams(
                collection_name=args.collection_name,
                create_collection_params=toCreateCollectionParams(args),
                bulk_index_params=toBulkIndexParams(args),
            )
        )
    )


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    setup_create_collection_parser(subparsers, "create_collection")
    setup_bulk_index_parser(subparsers, "bulk_index")
    setup_search_parser(subparsers, "search")
    setup_info_parser(subparsers, "info")
    setup_delete_collection_parser(subparsers, "delete_collection")
    # setup_recreate_collection_parser(subparsers, "recreate")

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
