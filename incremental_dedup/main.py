from vector_operations import VectorOperations
from clustering import ClusteringOperations, IncrementalClustering
from diff_operations import DiffOperations
from incremental_dedup.deduplicator import DeleteOperations

def auto_deduper():
    """
    Main entry point for running clustering and diff operations.
    Demonstrates usage of ClusteringOperations, IncrementalClustering, and DiffOperations.
    """
    # Initialize vector operations with Elasticsearch connection
    vector_ops = VectorOperations(
        elastic_address="http://localhost:9200",
        db_index="my-nested-index"
    )

    # Example 1: Basic clustering for a range of thresholds
    clustering = ClusteringOperations(vector_ops)
    thresholds = [round(0.81 + i * 0.01, 2) for i in range(7)]  # 0.81 to 0.87
    clustering.analyze_clustering(
        key="question.bge_search_vector",
        thresholds=thresholds,
        output_dir="output"
    )

    # Example 2: Incremental clustering (add a single item to clusters)
    incremental = IncrementalClustering(
        vector_ops=vector_ops,
        clusters_index="clusters"
    )
    incremental.add_to_cluster(
        item_id="9204070235430229",
        key="question.bge_search_vector"
    )

    # Example 3: Diff operations (compare cluster files and output unique clusters)
    diff_ops = DiffOperations()
    input_files = [f"output/cleaned_clusters_0.{i:02d}.json" for i in range(70, 91)]  # 0.70 to 0.90
    diff_ops.process_diff(
        input_files=input_files,
        output_file="output/diff-output.json"
    )

if __name__ == "__main__":
    auto_deduper() 