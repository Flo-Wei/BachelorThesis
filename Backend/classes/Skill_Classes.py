from pydantic import BaseModel, Field
from typing import Literal, Dict, List, Optional, Any


class BaseSkill(BaseModel):
    def export_to_schemaorg(self, language: str = "en") -> Dict[str, Any]:
        raise NotImplementedError

class CustomSkill(BaseSkill):
    name: str
    type: str  # Changed from Literal to str to be more forgiving with DB values
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(description="Direct quote or paraphrased section of the interview that supports the inference.")

    def export_to_schemaorg(self, language: str = "en") -> Dict[str, Any]:
        return {
            "@type": "DefinedTerm",
            "name": self.name,
            "description": self.evidence,
            "additionalType": self.type
        }

class ESCOSkill(BaseSkill):
    uri: str
    title: str
    reference_language: str
    preferred_label: Dict[str, str]
    description: Dict[str, str]
    links: dict

    def __str__(self) -> str:
        return self.title
    
    def __repr__(self) -> str:
        return self.title

    def get_preferred_label(self, language: Optional[str] = None) -> str:
        if language is None:
            language = self.reference_language
        return self.preferred_label.get(language, self.title)
    
    def get_description(self, language: Optional[str] = None) -> str:
        if language is None:
            language = self.reference_language
        return self.description.get(language, "No description available")
    
    def export_to_schemaorg(self, language: str = "en") -> Dict[str, Any]:
        return {
            "@type": "DefinedTerm",
            "termCode": self.uri,
            "name": self.get_preferred_label(language),
            "description": self.get_description(language),
            "inDefinedTermSet": {
                "@type": "DefinedTermSet",
                "name": "ESCO - European Skills, Competences, Qualifications and Occupations",
                "url": "https://esco.ec.europa.eu/",
            }
        }

 

class SkillList(BaseModel):
    skills: List[BaseSkill]

    def get_skill_by_id(self, id: int) -> BaseSkill:
        return self.skills[id]

class CustomSkillList(SkillList):
    skills: List[CustomSkill]

    def get_skill_by_id(self, id: int) -> CustomSkill:
        return self.skills[id]
