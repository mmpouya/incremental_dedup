# Incremental Deduplication
A Python library for efficient vector-based deduplication and clustering with incremental updates. This library helps identify and manage duplicate or similar items in large datasets using vector embeddings and clustering techniques.

## Overview
Incremental Deduplication provides tools for:

- Vector similarity calculations using cosine similarity
- Clustering similar items based on configurable thresholds
- Incremental updates to existing clusters
- Comparing clusters across different threshold settings
- Integration with Elasticsearch for scalable storage and retrieval
## Features
- Vector Operations : Extract and compare vector embeddings from Elasticsearch
- Clustering Operations : Group similar items into clusters based on vector similarity
- Incremental Clustering : Add new items to existing clusters without reprocessing the entire dataset
- Diff Operations : Compare clusters generated with different thresholds to identify unique clusters
- Elasticsearch Integration : Seamless interaction with Elasticsearch for storage and retrieval
## Installation
```
pip install -e .
```
Or install from the repository:

```
pip install git+https://github.com/mmpouya/incremental_dedup
incremental_dedup
```
## Requirements
- Python 3.6+
- Elasticsearch 8.x
- Pydantic
- OpenAI (for optional LLM-based similarity checking)
- texttools (from GitHub)
## Usage
### Basic Example
```
from incremental_dedup import VectorOperations, 
ClusteringOperations

# Initialize vector operations with Elasticsearch connection
vector_ops = VectorOperations(
    elastic_address="http://localhost:9200",
    db_index="my-index"
)

# Perform clustering with different thresholds
clustering = ClusteringOperations(vector_ops)
thresholds = [0.80, 0.85, 0.90]  # Similarity thresholds
clustering.analyze_clustering(
    key="question.bge_search_vector",
    thresholds=thresholds,
    output_dir="output"
)
```
### Incremental Clustering
```
from incremental_dedup import IncrementalClustering

# Initialize incremental clustering
incremental = IncrementalClustering(
    vector_ops=vector_ops,
    clusters_index="clusters"
)

# Add a new item to existing clusters
incremental.add_to_cluster(
    item_id="item123",
    key="question.bge_search_vector"
)
```
### Comparing Clusters
```
from incremental_dedup import DiffOperations

# Compare clusters generated with different thresholds
diff_ops = DiffOperations()
input_files = ["output/clusters_0.80.json", "output/
clusters_0.85.json"]
diff_ops.process_diff(
    input_files=input_files,
    output_file="output/diff-output.json"
)
```
## Architecture
The library consists of several key components:

1. 1.
   VectorOperations : Handles vector extraction and similarity calculations
2. 2.
   ClusteringOperations : Groups items into clusters based on vector similarity
3. 3.
   IncrementalClustering : Extends clustering with support for incremental updates
4. 4.
   DiffOperations : Compares clusters across different threshold settings
5. 5.
   ElasticsearchClient : Provides a wrapper for Elasticsearch operations
## Data Structure
The library expects documents in Elasticsearch to have vector embeddings stored in a nested structure, typically under a field like question.bge_search_vector or similar paths.

## License
This project is maintained by Givechi.

## Contributing
Contributions are welcome. Please feel free to submit a Pull Request.
