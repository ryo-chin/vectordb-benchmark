# vectordb-benchmark

## Setup

install python via pyenv(For Mac)
```shell
brew install pyenv
pyenv install # install version definend in .python-version
```

launch virtual environment
```shell
pip -m venv venv
. venv/bin/activate
```

launch qdrant docker container
```shell
docker compose up -d
```

launch locust
```shell
locust
```

## Qdrant

### setup
if you use Qdrant Cloud,
```shell
export QDRANT_API_KEY=${Qdrant api key}
export QDRANT_HOST=${Qdrant host}
```

### Create collection
```shell
python -m qdrant create_collection
```

### Bulk index
```shell
python -m qdrant bulk_index
```

### Search
```shell
python -m qdrant search
```

### Recreate and Benchmark
```shell
./qdrant_recreate_and_benchmark.sh
```

## Pinecone

### setup
```shell
export PINECONE_API_KEY=${Pinecone api key}
```

### Ceate index
From pincone GUI

### Bulk Index
```shell
python pinecone_commands/bulk_index.py
```

### Search
```shell
python pinecone_commands/search_test_vectors.py
```

