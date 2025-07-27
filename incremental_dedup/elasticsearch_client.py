from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from typing import Optional, List, Dict, Any

class ElasticsearchClient:
    """
    Base class for Elasticsearch operations, providing basic CRUD and search functionality.
    """
    # ELASTIC_ADDRESS = None
    # DB_INDEX = None
    
    def __init__(self, elastic_address: Optional[str] = "http://localhost:9200", db_index: str = "", *args, **kwargs):
        """
        Initialize the Elasticsearch client.
        Args:
            elastic_address (Optional[str]): Address of the Elasticsearch server.
            db_index (str): Name of the index to operate on.
        """
        self.elastic_address = elastic_address # or "http://localhost:9200"
        self.db_index = db_index
        self.args = args
        self.kwargs = kwargs
        self._connent_db()
        
        
    def _connent_db (self):
        self.client = Elasticsearch(self.elastic_address, self.kwargs)

    # def connection(self) -> Elasticsearch:
    #     return Elasticsearch(self.elastic_address)
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single document by ID.
        Args:
            item_id (str): The ID of the document to retrieve.
        
        Returns:
            Optional[Dict[str, Any]]: The document's _source dict if found, otherwise None.
        """
        try:
            response = self.client.get(index=self.db_index, id=item_id)
            # You can return the entire response or just the _source:
            return response.get("_source", {})
        except NotFoundError:
            # Document does not exist
            return None
    
    def search(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a search query on the configured index.
        Args:
            body (Dict[str, Any]): Elasticsearch query body.
        Returns:
            Dict[str, Any]: Search results.
        """
        return self.client.search(index=self.db_index, body=body)

    def update(self, doc_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a document by ID.
        Args:
            doc_id (str): Document ID to update.
            body (Dict[str, Any]): Update body (can include scripts or partial docs).
        Returns:
            Dict[str, Any]: Update response.
        """
        return self.client.update(index=self.db_index, id=doc_id, body=body)

    def index(self, doc_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index (create or replace) a document by ID.
        Args:
            doc_id (str): Document ID.
            body (Dict[str, Any]): Document body.
        Returns:
            Dict[str, Any]: Indexing response.
        """
        return self.client.index(index=self.db_index, id=doc_id, body=body)

    def get_all_documents(self, size: int = 200, source: List[str] = None) -> Dict[str, Any]:
        """
        Get all documents from the index, optionally filtering source fields.
        Args:
            size (int): Maximum number of documents to retrieve.
            source (List[str], optional): List of source fields to include.
        Returns:
            Dict[str, Any]: Search results containing all documents.
        """
        body = {
            "size": size,
            "query": {
                "match_all": {}
            }
        }
        if source:
            body["_source"] = source
        return self.search(body) 

