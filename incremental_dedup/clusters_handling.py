import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from incremental_dedup.vector_operations import SimilarIDs #,VectorOperations
from incremental_dedup.elasticsearch_client import ElasticsearchClient
from texttools.tools import GemmaQuestionMerger

class Relaxed(BaseModel):
    """Keep unknown keys, allow loose types, include extras on dump."""

    model_config = {
        "extra": "allow",
        "strict": False,
    }
  
class CosineClusterDoc (Relaxed):
    id: str 
    embedding_key: str
    min_threshold: float 
    similar_ids: List[str]
    

class CosineClusters:
    def __init__(self, elastic_client:ElasticsearchClient, merging_keys: List , AI_client:OpenAI, clusters_index: str = "similars"):
        """
        Initialize with a VectorOperations instance and cluster index name.
        Args:
            vector_ops (VectorOperations): Instance for vector and similarity operations.
            clusters_index (str): Name of the Elasticsearch index for clusters.
        """
        # self.item_id = item_id
        # self.similar_ids = similar_ids
        self.elastic_client = elastic_client
        self.client=AI_client
        self.merging_keys = merging_keys
        self.clusters_index = clusters_index
        
    def _retrieve_similar_ids (self, similar_ids:Dict) -> List:
        docs_list = []
        for item_id in similar_ids.keys():
            doc = self.elastic_client.get_item(item_id)
            docs_list.append(doc)
        return docs_list
    
    # def _process_duplicates (self, model_key: str,similar_ids:List)-> List[Dict]:
    #     clusters_dict = self._retrieve_similar_ids(similar_ids=similar_ids)
    #     # for cluster_dict in clusters_dict:
    #     #     sample_cluster_doc = {
    #     #         "id": str ,
    #     #         "embedding_model": str,
    #     #         "threshold": float ,
    #     #         "cluster_ids": List[str]
    #     #     }
    #     #     cluster_ids = cluster_dict["cluster_ids"]
        
    #     return clusters_dict 

    def _merge_dicts(self, d1:dict, d2:dict, model:str):
        """
        Merge two dictionaries. For keys that appear in both dictionaries,
        their values are combined into a list. Unique keys keep their original value.
        
        Args:
            d1 (dict): First input dictionary.
            d2 (dict): Second input dictionary.
            
        Returns:
            dict: A new dictionary with merged keys and values.
        """
        merged = {}
        merger = GemmaQuestionMerger(client=self.client, model=model ,use_reason=False)
        for key, value in d1.items():
            if key in d2:
                # If both values are already lists, extend them
                if key in self.merging_keys:
                    value2 = d2[key]
                    list_values = [value, value2]
                    merged_question = merger.merging_question(list_values)
                    merged[key] = merged_question
                else:
                # if key in self.merge_config.concat_keys:
                # if ther are some keys, not provided in config, the default approach in considering them as concat.
                    if isinstance(value, list):
                        combined = value.copy()
                    else:
                        combined = [value]
                    other = d2[key]
                    
                    if isinstance(other, list):
                        combined.extend(other)
                    else:
                        combined.append(other)
                    merged[key] = combined                
            else:
                # Unique to d1
                merged[key] = value
        # Add keys that are only in d2
        for key, value in d2.items():
            if key not in merged:
                merged[key] = value
        return merged
    
    def merge_duplicates(self, cluster_dict: CosineClusterDoc, model:str = "gemma-3") -> QARecord:
        docs = self._retrieve_similar_ids(similar_ids=cluster_dict.similar_ids)
        based_doc = self.elastic_client.get_item(cluster_dict.id)
        if based_doc:
            for item_dict in docs:
                based_doc = self._merge_dicts(based_doc, item_dict, model=model)
                return based_doc
            pass
        if not based_doc:
            print("the cluster id match with no item in db. it is needed for overwriting the merged one.")
            return
    
    def remove_duplicates(self, cluster_dict: CosineClusterDoc) -> None:
        '''
        not developed yet
        '''
        if not cluster_dict:
            return
        docs = self._retrieve_similar_ids(similar_ids=cluster_dict.similar_ids)
        # remove
        pass
            
        