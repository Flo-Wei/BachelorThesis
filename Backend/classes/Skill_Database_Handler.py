from abc import ABC, abstractmethod
from typing import List
import requests
from Skill_Classes import ESCOSkill


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
        response = requests.get(url, params=params)

        skill_list = []
        for skill in response.json()["_embedded"]["results"]:
            skill_list.append(ESCOSkill(
                uri=skill["uri"],
                title=skill["title"],
                reference_language=skill["referenceLanguage"][0],
                preferred_label=skill["preferredLabel"],
                description={desc[0]: desc[1]["literal"] for desc in skill["description"].items()},
                links=skill["_links"]
            ))
        return skill_list
