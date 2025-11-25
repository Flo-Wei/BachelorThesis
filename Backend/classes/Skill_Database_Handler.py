from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from Backend.classes.Skill_Classes import ESCOSkill


class BaseSkillDatabaseHandler(ABC):
    def __init__(self, url: str):
        self.url = url

class ESCODatabase(BaseSkillDatabaseHandler):
    def __init__(self, 
        url: str ="https://ec.europa.eu/esco/api",
        language: str = "en"
    ):
        super().__init__(url.rstrip('/'))
        self.language = language

    def search_skills(self, text: str, limit: int = 20) -> List[ESCOSkill]:
        url = f"{self.url}/search"
        params = {
            "text": text,
            "language": self.language,
            "type": "skill",
            "limit": limit,
            "full": True
        }
        response = requests.get(url, params=params, timeout=10)

        skill_list = []
        if response.status_code == 200 and "_embedded" in response.json():
            for skill in response.json()["_embedded"]["results"]:
                # Ensure links dict is available and copy broaderHierarchyConcept if present
                links = skill.get("_links", {})
                if "broaderHierarchyConcept" in skill:
                    links["broaderHierarchyConcept"] = skill["broaderHierarchyConcept"]
                if "broaderSkill" in skill:
                    links["broaderSkill"] = skill["broaderSkill"]
                
                skill_list.append(ESCOSkill(
                    uri=skill["uri"],
                    title=skill["title"],
                    reference_language=skill["referenceLanguage"][0],
                    preferred_label=skill["preferredLabel"],
                    description={desc[0]: desc[1]["literal"] for desc in skill["description"].items()},
                    links=links
                ))
        return skill_list

    def get_skill_details(self, uri: str) -> Dict[str, Any]:
        """
        Fetch full details for a specific skill URI from ESCO API.
        """
        url = f"{self.url}/resource/skill"
        params = {
            "uri": uri,
            "language": self.language
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching skill details for {uri}: {e}")
        return {}

    def get_occupation_details(self, uri: str) -> Dict[str, Any]:
        """
        Fetch full details for a specific occupation URI from ESCO API.
        """
        url = f"{self.url}/resource/occupation"
        params = {
            "uri": uri,
            "language": self.language
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching occupation details for {uri}: {e}")
        return {}

    def get_related_occupations(self, uris: List[str]) -> Dict[str, Any]:
        """
        Aggregate occupations for a list of skill URIs.
        Returns a dictionary of occupations with counts.
        Uses parallel fetching for better performance.
        """
        occupations = {}
        
        def process_skill_uri(uri):
            """Process a single skill URI and return its occupations."""
            skill_occupations = {}
            details = self.get_skill_details(uri)
            if not details or "_links" not in details:
                return skill_occupations
            
            links = details["_links"]
            # Check for essential and optional occupations
            for rel_type in ["isEssentialForOccupation", "isOptionalForOccupation"]:
                if rel_type in links:
                    items = links[rel_type]
                    # API might return a single dict or list of dicts
                    if isinstance(items, dict):
                        items = [items]
                    
                    for item in items:
                        occ_uri = item.get("uri")
                        title = item.get("title", "Unknown")
                        if occ_uri:
                            if occ_uri not in skill_occupations:
                                skill_occupations[occ_uri] = {
                                    "title": title,
                                    "uri": occ_uri,
                                    "count": 0,
                                    "relations": []
                                }
                            skill_occupations[occ_uri]["count"] += 1
                            skill_occupations[occ_uri]["relations"].append({
                                "skill_uri": uri,
                                "type": rel_type
                            })
            return skill_occupations
        
        # Process all URIs in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_skill_uri, uri): uri for uri in uris}
            for future in as_completed(futures):
                skill_occs = future.result()
                # Merge into main occupations dict
                for occ_uri, occ_data in skill_occs.items():
                    if occ_uri not in occupations:
                        occupations[occ_uri] = occ_data
                    else:
                        occupations[occ_uri]["count"] += occ_data["count"]
                        occupations[occ_uri]["relations"].extend(occ_data["relations"])
        
        return occupations
