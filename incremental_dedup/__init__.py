from incremental_dedup.vector_operations import VectorOperations
from incremental_dedup.clustering import ClusteringOperations, IncrementalClustering
from incremental_dedup.diff_operations import DiffOperations
from incremental_dedup.elasticsearch_client import ElasticsearchClient
from incremental_dedup.main import auto_deduper
# from incremental_dedup.deduplicator import DeleteOperations
from incremental_dedup.clusters_handling import CosineClusters

__version__ = '0.1.2'

__all__ = [
    "VectorOperations",
    "ClusteringOperations",
    "IncrementalClustering",
    "DiffOperations",
    "ElasticsearchClient",
    "auto_deduper",
    "DeleteOperations",
    "CosineClusters",
    ]