LOG_FILE="benchmark_results/qdrant_recreate_and_benchmark_$(date +%Y%m%d%H%M%S).log"

# 必要に応じてパラメーターを変更しながら実行する
VECTOR_SIZE=256
SHARD_NUMBER=1
REPLICA_NUMBER=1
INDEX_THRESHOLD=5000
HOST=http://localhost:6333
if [ -n "$QDRANT_HOST" ]; then
    HOST=$QDRANT_HOST
fi

recreate() {
    local INDEX_NUM=$1
    python -m qdrant delete_collection
    python -m qdrant create_collection \
        --vector_size $VECTOR_SIZE \
        --shard_number $SHARD_NUMBER \
        --replica_number $REPLICA_NUMBER \
        --on_disk true
    python -m qdrant bulk_index \
        --vector_size $VECTOR_SIZE \
        --index_num $INDEX_NUM \
        --index_threshold $INDEX_THRESHOLD \
        --parallel_count 4 | tee -a "$LOG_FILE"
    # python -m qdrant bulk_index \
    #     --vector_size $VECTOR_SIZE \
    #     --index_num $INDEX_NUM \
    #     --index_threshold $INDEX_THRESHOLD \
    #     --parallel_count 4
    python -m qdrant info | tee -a "$LOG_FILE"
}

for INDEX_NUM in 10000
# for INDEX_NUM in 10000 50000
# for INDEX_NUM in 10000 50000 100000
# for INDEX_NUM in 1000000
# for INDEX_NUM in 10000000
do
    recreate $INDEX_NUM
    TOP_K=10 LOCUST_USERS=30 LOCUST_EXPECT_WORKERS=30 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    TOP_K=100 LOCUST_USERS=30 LOCUST_EXPECT_WORKERS=30 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    TOP_K=10 LOCUST_USERS=100 LOCUST_EXPECT_WORKERS=100 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    TOP_K=100 LOCUST_USERS=100 LOCUST_EXPECT_WORKERS=100 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    TOP_K=10 LOCUST_USERS=1000 LOCUST_EXPECT_WORKERS=1000 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    TOP_K=100 LOCUST_USERS=1000 LOCUST_EXPECT_WORKERS=1000 locust --config qdrant_benchmark.conf --host $HOST --skip-log | tee -a "$LOG_FILE"
    echo "finish benchmark INDEX_NUM=$INDEX_NUM on_disk true" | tee -a "$LOG_FILE"
done