from openai import OpenAI
from openai.types.responses.response import Response as OpenAIResponse
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from ModelConfigClasses import ModelConfigOpenAI, ModelConfig
from util_classes import ChatHistory, LLMMessage, BaseSkill, CustomSkill, CustomSkillList
from utils import get_prompt

class BaseLLM(ABC):
    def __init__(self, model_name: str, config: ModelConfig):
        self.model_name: str = model_name
        self.config: ModelConfig = config
    
    @abstractmethod
    def chat(
        self, 
        chat_history: ChatHistory
    ) -> LLMMessage:
        pass
    
    @abstractmethod
    def extract_skills(
        self,
        instruction: str,
        messages: LLMMessage
    ) -> List[CustomSkill]:
        pass

    @abstractmethod
    def map_skill(
        self,
        instruction: str,
        skill: CustomSkill,
        available_skills: List[BaseSkill]
    ) -> BaseSkill:
        pass


class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str, config: ModelConfigOpenAI):
        super().__init__(model_name, config)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=api_key)

    def chat(
        self, 
        chat_history: ChatHistory) -> LLMMessage: 

        config = self.config.to_dict()
        response = self.client.responses.create(
            model=self.model_name,
            messages=chat_history.to_openai_input(),
            **config
        )
        return LLMMessage.from_openai_message(response)

    def extract_skills(
        self,
        instruction: str,
        messages: LLMMessage
    ) -> List[CustomSkill]:
        response = self.client.responses.parse(
            model=self.model_name,
            input=[
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": messages.content,
                },
            ],
            text_format=CustomSkillList,
        )
        return response.output_parsed.skills
    
    def map_skill(
        self,
        instruction: str,
        skill: CustomSkill,
        available_skills: List[BaseSkill]
    ) -> BaseSkill:
        
        mapping_prompt = get_prompt("information_mapper").format(skill=skill, available_skills=available_skills.to_json())
        
        response = self.client.responses.create(
            model=self.model_name,
            input=mapping_prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "skill_id",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "The ID of the best matching skill from the available skills list."
                            }
                        },
                        "required": ["id"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        )
        
        return available_skills.get_skill_by_id(response.output_text["id"])