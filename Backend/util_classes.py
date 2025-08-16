from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, List
from datetime import datetime
from openai.types.responses.response import Response as OpenAIResponse

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
    className: str
    uri: str
    searchHit: str
    title: str
    preferredLabel: Dict[str, str]
    isTopConceptInScheme: List[str]
    isInScheme: List[str]
    hasSkillType: List[str]
    hasReuseLevel: List[str]
    broaderHierarchyConcept: List[str]

class SkillList(BaseModel):
    skills: List[BaseSkill]

class CustomSkillList(SkillList):
    skills: List[CustomSkill]