from typing import List, Dict, Any, Optional
import json
import time

from openai import OpenAI
from pydantic import BaseModel
from vector_operations import VectorOperations, SimilarIDs
from elasticsearch_client import ElasticsearchClient
from clusters_handling import CosineClusterDoc

class ThresholdDoc(BaseModel):
    safe: float
    min: float
    pass

class ClusteringOperations:
    """
    Handles clustering operations for grouping items based on vector similarity.
    Uses a provided VectorOperations instance to compute similarities and manage clusters.
    """

    def __init__(self, vector_ops: VectorOperations):
        """
        Initialize with a VectorOperations instance.
        Args:
            vector_ops (VectorOperations): Instance for vector and similarity operations.
        """
        self.vector_ops = vector_ops
        self.similarity_cache = {}  # Cache to store computed similarities for efficiency
        self.total_similarity_time = 0.0  # Total time spent on similarity calculations
        self.similarity_count = 0  # Number of similarity calculations performed

    def cluster_items(self, item_id: str, key: str, threshold: float, clusters: List[List[str]]) -> List[List[str]]:
        """
        Cluster a single item into existing clusters or create a new cluster based on similarity scores.
        Args:
            item_id (str): The ID of the item to cluster.
            key (str): The embedding key to use for similarity.
            threshold (float): Similarity threshold for clustering.
            clusters (List[List[str]]): Current list of clusters.
        Returns:
            List[List[str]]: Updated list of clusters.
        """
        if item_id not in self.similarity_cache:
            t1 = time.time()
            similarity = self.vector_ops.evaluate_similarity(item_id, key)
            #________________________________________
            if similarity is None:
                # If similarity can't be computed, skip clustering for this item
                return clusters
            #________________________________________
            self.similarity_cache[item_id] = similarity
            t2 = time.time()
            self.total_similarity_time += t2 - t1
            self.similarity_count += 1

        similarity_scores = self.similarity_cache[item_id].get(item_id, {})
        matched = False

        # Try to add the item to an existing cluster if similarity exceeds threshold
        for cluster in clusters:
            for id in cluster:
                score = similarity_scores.get(id)
                if score is None and id in self.similarity_cache:
                    # Try reverse lookup if not found in direct similarity
                    revers = self.similarity_cache[id].get(id, {})
                    score = revers.get(item_id)

                if score is not None and score >= threshold:
                    cluster.append(item_id)
                    matched = True
                    break

            if matched:
                break

        if not matched:
            # If not similar to any cluster, create a new cluster
            clusters.append([item_id])

        return clusters

    def analyze_clustering(self, key: str, thresholds: List[float], output_dir: str = "") -> None:
        """
        Process clustering for a list of thresholds, saving results for each threshold.
        Args:
            key (str): Embedding key to use for similarity.
            thresholds (List[float]): List of similarity thresholds to try.
            output_dir (str): Directory to save output files.
        """
        #________________________________________
        # This part wasn't designed as a function, and I thought it would be a waste.
        # That's why I made it a function and kept it.
        items = self.vector_ops.extract_vectors(key)
        id_list = [item["id"] for item in items if "id" in item]

        questions = self.vector_ops.extract_questions()
        id_to_question = {q["id"]: q["question"] for q in questions if "id" in q and "question" in q}

        for threshold in thresholds:
            self.similarity_cache = {}
            self.total_similarity_time = 0.0
            self.similarity_count = 0
            clusters = []

            for id in id_list:
                clusters = self.cluster_items(id, key, threshold, clusters)

            avg_time = self.total_similarity_time / self.similarity_count if self.similarity_count else 0.0
            print(f"[{threshold:.2f}] Total time: {self.total_similarity_time:.3f}s | Avg per item: {avg_time:.3f}s")

            # Prepare output: map cluster index to list of item dicts (id, question)
            output = {
                f"clusters_{i+1}": [
                    {"id": item_id, "question": id_to_question.get(item_id, "N/A")}
                    for item_id in clus
                ]
                for i, clus in enumerate(clusters) if clus
            }

            filename = f"{output_dir}/clustering_{threshold:.2f}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            # Generate cleaned clusters (remove singletons)
            cleaned_output = self.clean_clusters(output)
            clean_filename = f"{output_dir}/cleaned_clusters_{threshold:.2f}.json"
            with open(clean_filename, "w", encoding="utf-8") as f:
                json.dump(cleaned_output, f, indent=2, ensure_ascii=False)

        print("All files generated.")

    @staticmethod
    def clean_clusters(cluster_output: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
        """
        Remove clusters with only one member (singletons) from the output.
        Args:
            cluster_output (Dict[str, List[Dict[str, str]]]): Cluster output mapping.
        Returns:
            Dict[str, List[Dict[str, str]]]: Cleaned cluster output.
        """
        return {
            key: members
            for key, members in cluster_output.items()
            if isinstance(members, list) and len(members) > 1
        }

class IncrementalClustering(ClusteringOperations):
    """
    Handles incremental clustering operations, allowing items to be added to clusters one at a time.
    Extends ClusteringOperations with Elasticsearch-based cluster management.
    """

    def __init__(self, vector_ops: VectorOperations, clusters_index: str = "clusters", thresholds = None ):
        """
        Initialize with a VectorOperations instance and cluster index name.
        Args:
            vector_ops (VectorOperations): Instance for vector and similarity operations.
            clusters_index (str): Name of the Elasticsearch index for clusters.
        """
        super().__init__(vector_ops)
        self.clusters_index = clusters_index
        # Thresholds for different embedding keys
        self.thresholds = thresholds or {
            "question.bge_search_vector": {"max": 0.89, "min": 0.70},
            "question.e5_search_vector": {"max": 0.99, "min": 0.88}
        }

    def add_to_cluster(self, item_id: str, key: str) -> List:
        """
        Add an item to an existing cluster if similar, or create a new cluster if not.
        Args:
            item_id (str): The ID of the item to add.
            key (str): The embedding key to use for similarity.
        return:
            List of ids of all duplicated items
            None if bug
        """
        max_threshold = self.thresholds.get(key, {}).get("max")
        if max_threshold is None:
            print(f"No threshold is determined for key: {key}")
            print(f"using default threshhold.")
            print(f"default threshholds: max= 0.9 min= 0.8")
            max_threshold = 0.9

        similarity = self.vector_ops.evaluate_similarity(item_id, key)
        if similarity is None:
            # If similarity can't be computed, skip
            return
            
        similarity_scores = similarity.get(item_id, {})
        # Find all IDs with similarity above threshold
        similar_ids = {id for id, score in similarity_scores.items() if score >= max_threshold}

        # Search for existing clusters in Elasticsearch
        result = self.vector_ops.get_all_documents(size=10000)
        clusters = result["hits"]["hits"]

        existing_cluster_id = None
        existing_ids = set()

        for cluster in clusters:
            cluster_id = cluster["_id"]
            existing_ids.add(int(cluster_id))
            cluster_ids = set(cluster["_source"].get("cluster_ids", []))

            if item_id in cluster_ids:
                print(f"Item {item_id} already exists in cluster {cluster_id}.")
                return

            if similar_ids & cluster_ids:
                # If any similar ID is already in a cluster, mark this cluster for update
                existing_cluster_id = cluster_id

        if existing_cluster_id:
            # Update existing cluster to add the new item
            self.vector_ops.update(existing_cluster_id, {
                "script": {
                    "source": "if (!ctx._source.cluster_ids.contains(params.id)) { ctx._source.cluster_ids.add(params.id) }",
                    "lang": "painless",
                    "params": {"id": item_id}
                }
            })
            print(f"Item {item_id} added to existing cluster {existing_cluster_id}.")

        elif similar_ids:
            # Create a new cluster if there are similar items but no existing cluster
            new_id = str(max(existing_ids) + 1) if existing_ids else "1"
            all_ids = list(similar_ids | {item_id})
            if len(all_ids) > 1:
                new_cluster_doc = {
                    "id": new_id,
                    "key": key.split(".")[1],
                    "threshold": max_threshold,
                    "cluster_ids": all_ids
                }
                self.vector_ops.index(new_id, new_cluster_doc)
                print(f"New cluster {new_id} created with items: {all_ids}")
            else:
                print("Not enough similar items; cluster not created.")
        else:
            print("No similar items found; cluster not created.")
            
class CosineClusterer:
    def __init__(self, AI_client: OpenAI , elastic_client:ElasticsearchClient, threshold: Optional[Dict[str,ThresholdDoc]]):
        self.client = AI_client
        self.elastic_client = elastic_client
        self.threshold = threshold

    def _LLM_similarity_check(self, item_id1, item_id2, model: Optional[str]= "gemma-3", **client_kwargs)-> bool:
        '''
        Uses an LLM to check if all questions in the list have exactly the same meaning.

        Args:
            questions (List[str]): A list of questions to check.

        Returns:
            bool: True if all questions have the same meaning, False otherwise.
        this code is provided by Mrs. Aliyari
        '''   
        questions = []
        for id in [item_id1, item_id2]:
            result = self.elastic_client.search(index="new_index", body={
        "size": 1,
        "_source": ["question.text"],
            "query": {
                "term": {
                    "elastic_id": id
                }
            }
    })
            hits = result.get("hits", {}).get("hits", [])
            if hits:
                question_text = hits[0]["_source"]["question"]["text"]

            # Extract question text whether it's stored as a dict or a string
            text_obj = hits[0]["_source"]["question"]["text"]     
            if isinstance(text_obj, dict):
                question_text = next(iter(text_obj.values()))
            else:
                question_text = text_obj
                
                questions.append(question_text)      
        system_prompt = "You are a semantic clustering assistant."
        user_prompt = (
            f"List of questions: {questions}.\n"
            "Do all these questions have exactly the same meaning?\n"
            "Answer only with 'true' or 'false'."
        )

        # Call the LLM using the Generate function
        raw_response = self.client.chat.completions.create(
            model=model,
            messages= [
                {
                    "role": "system",
                    "content":system_prompt,
                    },
                {
                    "role": "user",
                    "content":user_prompt,
                    }
            ],
            **client_kwargs
            )
        response:str = raw_response.choices[0].message.content
        
        # Return True if the LLM responds exactly with 'true' (case-insensitive)
        if response:
            if response.strip().lower() == "true" or response.strip().lower().startswith("true"):
                return True
            if response.strip().lower() == "false" or response.strip().lower().startswith("false"):
                return False
        else:
            return
        
    def cluster_process(self, similarity_doc: SimilarIDs) -> CosineClusterDoc:
        embedding_key:str= similarity_doc.embedding_key
        embedding_path= "question." + embedding_key
        
        try:
            safe_threshold = self.threshold.get(embedding_key).get("safe")
            min_threshold = self.threshold.get(embedding_key).get("min")
        except:
            print(f"no threshold has been provided for {embedding_key}")
            print("based on nothing, thresholds 0.9 and 0.8 will be considered as safe and min")
            safe_threshold = 0.9
            min_threshold = 0.8
        min = 0.0
        similar_ids = []
        
        for sim_id, score in similarity_doc.similar_id.items():
            if score >= safe_threshold:
                similar_ids.append(sim_id)
                min = score
            elif min_threshold <= score < safe_threshold:
                response = self._LLM_similarity_check(similarity_doc.id, sim_id, model="gemma3")
                if response == True:
                    similar_ids.append(sim_id)
                    min = score
            else:
                f"this {sim_id} is irrevelent!"
                pass
        '''
        add to elastic in "similars" index a SimilarIDs object
        provided by Ms. Aliyari
        '''
        if similar_ids:     
            doc = {
            "id": similarity_doc.id,
            "embedding_key": embedding_key,
            "min_threshold":  min,
            "similar_ids": similar_ids
            }
            ElasticsearchClient.index(index="similars", id=str(similarity_doc.id),  document=doc)
            print(f"Document of a similarity is indexed with ID: {similarity_doc.id}")
        cleaned_doc = similarity_doc
        # cleaned_doc.pop()
        cleaned_doc["min_threshold"] =  min
        cleaned_doc["similar_ids"] =  similar_ids
        # change to CosineClusterDoc (BaseModel):
                # id: str 
                # embedding_key: str
                # min_threshold: float 
                # similar_ids: List[str]
        return cleaned_doc
                