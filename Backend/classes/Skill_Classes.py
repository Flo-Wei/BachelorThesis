from pydantic import BaseModel, Field
from typing import Literal, Dict, List, Optional


class BaseSkill(BaseModel):
    pass

class CustomSkill(BaseSkill):
    name: str
    type: Literal["technical", "soft", "domain-specific", "other"]
    confidence: float = Field(ge=0, le=1)
    evidence: str = Field(description="Direct quote or paraphrased section of the interview that supports the inference.")

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
 

class SkillList(BaseModel):
    skills: List[BaseSkill]

    def get_skill_by_id(self, id: int) -> BaseSkill:
        return self.skills[id]

class CustomSkillList(SkillList):
    skills: List[CustomSkill]

    def get_skill_by_id(self, id: int) -> CustomSkill:
        return self.skills[id]
