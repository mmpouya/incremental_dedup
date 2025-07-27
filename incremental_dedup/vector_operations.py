from typing import List, Dict, Any, Optional
from elasticsearch_client import ElasticsearchClient
from pydantic import BaseModel

class SimilarIDs(BaseModel):
    id: str | int
    embedding_key: str
    similar_id: Dict[str|int, float]

class VectorOperations:
    """
    Handles vector extraction and similarity calculations.
    Extends ElasticsearchClient to provide vector-specific operations for clustering and search.
    """
    def __init__(self, elastic_client: ElasticsearchClient, elastic_address:Optional[str] , db_index = ""):
        self.elastic_client = elastic_client
        if not elastic_address:
            self.elastic_address = "http://localhost:9200"
        
    
    def extract_all_vectors(self, embedding_key: str, size: int = 10) -> List[Dict[str, List]]:
        """
        Extract vectors for a given embedding key for all items in the index.
        Args:
            embedding_key (str): The key in the document containing the vector.
            size (int): Number of items to retrieve (default: 10).
        Returns:
            List[Dict[str, List]]: List of dicts with 'id' and 'vector' for each item.
        """
        source = ["elastic_id", embedding_key]
        body = {
            "size": size,
            "_source": source,
            "query": {
                "match_all": {}
            }
        }

        result = self.elastic_client.search(body)
        # result is an elastic object
        final_result = []
        
        key = embedding_key.split(".")[1]
        for answer in result["hits"]["hits"]:
            vector_dict = {
                "id": answer["_source"]["elastic_id"],
                "vector": answer["_source"]["question"][key]
            }
            final_result.append(vector_dict)

        return final_result

    def evaluate_similarity(self, item_id: str, embedding_key: str, target_vector: Optional[List]) -> Optional[SimilarIDs]:
        """
        Calculate cosine similarity between a given item and all others in the index.
        Args:
            item_id (str): The ID of the item to compare.
            embedding_key (str): The key in the document containing the vector.
        Returns:
            Optional[Dict[str, Dict[str, float]]]: Mapping from item_id to dict of {other_id: similarity}.
        """
        model_name = embedding_key.split(".")[1]
        # Get target vector for the specified item
        if not target_vector:
            response_vector = self.elastic_client.search({
            "size": 1,
            "_source": [embedding_key],
            "query": {
                "match": {
                    "elastic_id": item_id
                }
            }
        })

            if not response_vector["hits"]["hits"]:
                print({item_id: {"error": f"Item with id {item_id} has no embedding vector for {embedding_key}."}})
                return None

            
            target_vector = response_vector["hits"]["hits"][0]["_source"]["question"][model_name]

        # Calculate similarities to all other items using Elasticsearch script_score
        body = {
            "size": 10,
            "_source": ["elastic_id"],
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": f"cosineSimilarity(params.query_vector, '{embedding_key}') + 1.0",
                        "params": {
                            "query_vector": target_vector
                        }
                    }
                }
            }
        }

        response = self.elastic_client.search(body)
        similarities = {
            hit["_source"]["elastic_id"]: hit["_score"] - 1.0
            for hit in response["hits"]["hits"]
            if hit["_source"]["elastic_id"] != item_id
        }
        # Return a dict mapping the item_id to a sorted dict of similarities
        x:SimilarIDs = {
            "id": item_id,
            "embedding_key": model_name,
            "similar_id": dict(sorted(similarities.items(), key=lambda x: x[1], reverse=True))
        }
        return x

    def extract_all_questions(self, size: int = 200) -> List[Dict[str, str]]:
        """
        Extract questions (text) from the index for all items.
        Args:
            size (int): Number of items to retrieve (default: 200).
        Returns:
            List[Dict[str, str]]: List of dicts with 'id' and 'question.text' for each item.
        """
        result = self.elastic_client.get_all_documents(
            size=size,
            source=["elastic_id", "question.text"]
        )

        final_result = []
        for answer in result["hits"]["hits"]:
            source = answer["_source"]
            text_dict = source.get("question", {}).get("text", {})
            text = " ".join(text_dict.values()) # Concatenate all text fields

            final_result.append({
                "id": source.get("elastic_id"),
                "question": text
            })

        return final_result 