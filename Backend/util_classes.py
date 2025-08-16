from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List
from abc import ABC, abstractmethod
from datetime import datetime
from openai.types.responses.response import Response as OpenAIResponse
import requests

class LLMUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int

    def get_total_tokens(self):
        return self.prompt_tokens + self.completion_tokens

    def get_prompt_tokens(self):
        return self.prompt_tokens

    def get_completion_tokens(self):
        return self.completion_tokens

class LLMMessage(BaseModel):
    role: Literal["system", "assistant", "user"]
    content: str
    created_at: datetime
    model: str
    usage: LLMUsage

    def __str__(self):
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} {self.role}: {self.content}"
    
    def __repr__(self):
        return f"LLMMessage(role={self.role}, content={self.content}, created_at={self.created_at})"

    @classmethod
    def from_openai_message(cls, message: OpenAIResponse):
        return cls(
            role=message.output[0].role,
            content=message.output[0].content[0].text,
            created_at=datetime.fromtimestamp(message.created_at),
            model=message.model,
            usage=LLMUsage(
                prompt_tokens=message.usage.input_tokens,
                completion_tokens=message.usage.output_tokens,
            )
        )

class ChatHistory(BaseModel):
    messages: list[LLMMessage]
    created_at: datetime
    updated_at: datetime

    def __str__(self):
        return "\n".join([str(message) for message in self.messages])
    
    def __repr__(self):
        return f"ChatHistory(messages={self.messages}, created_at={self.created_at}, updated_at={self.updated_at})"

    def add_message(self, message: LLMMessage) -> None:
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages(self, role: Literal["system", "assistant", "user", "all"] = "all") -> list[LLMMessage]:
        if role == "all":
            return self.messages
        elif role == "system":
            return [message for message in self.messages if message.role == "system"]
        elif role == "assistant":
            return [message for message in self.messages if message.role == "assistant"]
        elif role == "user":
            return [message for message in self.messages if message.role == "user"]

    def get_last_message(self, role: Literal["system", "assistant", "user", "all"] = "all") -> LLMMessage | None:
        if role == "all":
            return self.messages[-1] if self.messages else None
        elif role == "system":
            return [message for message in self.messages if message.role == "system"][-1] if self.messages else None
        elif role == "assistant":
            return [message for message in self.messages if message.role == "assistant"][-1] if self.messages else None
        elif role == "user":
            return [message for message in self.messages if message.role == "user"][-1] if self.messages else None

    def get_usage(self) -> LLMUsage:
        return LLMUsage(
            prompt_tokens=sum([message.usage.prompt_tokens for message in self.messages]),
            completion_tokens=sum([message.usage.completion_tokens for message in self.messages]),
        )
    
    def to_openai_input(self) -> list[dict]:
        messages: list[dict] = []
        for message in self.messages:
            messages.append({
                "role": message.role,
                "content": [
                    {
                        "type": "input_text",
                        "text": message.content
                    }
                ]
            })
        return messages

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

    def get_preferred_label(self, language: str) -> str:
        return self.preferred_label.get(language, self.title)
    
    def get_description(self, language: str) -> str:
        return self.description.get(language, "No description available")
 

class SkillList(BaseModel):
    skills: List[BaseSkill]

    def to_json(self) -> str:
        pass
    
    def get_skill_by_id(self, id: int) -> BaseSkill:
        return self.skills[id]

class CustomSkillList(SkillList):
    skills: List[CustomSkill]

class ESCOSkillList(SkillList):
    skills: List[ESCOSkill]

    def to_json(self, language: str = "en") -> str:
        string = "["
        for i, skill in enumerate(self.skills):
            string += f"{{\n"
            string += f"\t\"id\": {i},\n"
            string += f"\t\"title\": \"{skill.get_preferred_label(language)}\",\n"
            string += f"\t\"description\": \"{skill.get_description(language)}\"\n"
            string += f"}}"
            if i < len(self.skills) - 1:
                string += ",\n"
        string += "]"
        return string

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
