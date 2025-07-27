# incremental_dedup

## Overview

`incremental_dedup` is a Python toolkit for clustering and deduplication of items (such as questions or documents) using vector similarity, with support for incremental clustering and integration with Elasticsearch. It provides tools to:
- Extract vectors and text from an Elasticsearch index
- Cluster items based on vector similarity
- Incrementally add items to clusters
- Compare and diff cluster results across thresholds

## Features
- **ClusteringOperations**: Groups items into clusters based on vector similarity.
- **IncrementalClustering**: Adds items to clusters one at a time, updating clusters in Elasticsearch.
- **DiffOperations**: Compares cluster files to find unique clusters.
- **VectorOperations**: Extracts vectors and computes similarities using Elasticsearch.
- **ElasticsearchClient**: Basic Elasticsearch CRUD/search operations.

<!-- 
## Usage

### Example: Running Main Operations

The main entry point is `main.py`, which demonstrates clustering, incremental clustering, and diff operations:

```bash
python main.py
```

This will:
- Connect to Elasticsearch (default: `http://localhost:9200`, index: `my-nested-index`)
- Run clustering for a range of thresholds and save results to `output/`
- Add a sample item to clusters incrementally
- Compare cluster files and output unique clusters -->

### Example: Using Classes Directly

See `example_usage.py` for a detailed walkthrough. Example snippet:

## Requirements
- Python 3.8+
- elasticsearch Python package
- An Elasticsearch instance running and accessible

## File Descriptions
- `main.py`: Main entry point, demonstrates core operations
- `example_usage.py`: Example usage of all main classes
- `clustering.py`: Clustering logic and incremental clustering
- `vector_operations.py`: Vector extraction and similarity calculations
- `elasticsearch_client.py`: Basic Elasticsearch operations
- `diff_operations.py`: Cluster diffing utilities

## Notes
- The codes on main.py and example_usage.py expect an Elasticsearch index with documents containing vector fields (e.g., `question.bge_search_vector`).
- Output directories (e.g.,`output/`) must exist or be created before running scripts that write files.
- For demo purposes, some example scripts handle missing Elasticsearch gracefully.


