import json
from typing import List, Dict, Any

class DiffOperations:
    """
    Handles diff operations between cluster files, allowing comparison and extraction of unique clusters.
    """

    @staticmethod
    def compare_clusters(input_files: List[str]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Compare multiple cluster files and find clusters that are unique to each file.
        Args:
            input_files (List[str]): List of file paths to cluster JSON files.
        Returns:
            Dict[str, Dict[str, List[Dict[str, Any]]]]: Mapping from file to its unique clusters.
        """
        data = {}
        for f in input_files:
            with open(f, "r", encoding="utf-8") as file:
                data[f] = json.load(file)

        cluster_map = {}
        # Map each cluster (as a string) to its file and key
        for f, clusters in data.items():
            for key, value in clusters.items():
                value_str = json.dumps(value, sort_keys=True, ensure_ascii=False)
                cluster_map.setdefault(value_str, []).append((f, key))

        output = {}
        # Only keep clusters that appear in a single file
        for value_str, locations in cluster_map.items():
            if len(locations) == 1:
                f, key = locations[0]
                output.setdefault(f, {})[key] = json.loads(value_str)

        return output

    def process_diff(self, input_files: List[str], output_file: str) -> None:
        """
        Process diff between multiple files and save results to output_file.
        Args:
            input_files (List[str]): List of file paths to compare.
            output_file (str): Path to save the diff results.
        """
        output = self.compare_clusters(input_files)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"Diff results saved to {output_file}") 