from openai import OpenAI
from openai.types.responses.response import Response as OpenAIResponse
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List
from sqlmodel import Session
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.models.skills import ChatSkillBase, ESCOSkillModel
from Backend.classes.Model_Config import ModelConfigOpenAI, ModelConfig
from Backend.classes.Skill_Classes import BaseSkill, CustomSkill, ESCOSkill, CustomSkillList
from Backend.utils import get_prompt
import logging
import json

class BaseLLM(ABC):
    def __init__(self, model_name: str, config: Optional[ModelConfig] = None):
        self.model_name: str = model_name
        self.config: Optional[ModelConfig] = config
    
    @abstractmethod
    def chat(
        self, 
        chat_session: ChatSession,
        db_session: Session
    ) -> ChatMessage:
        pass
    
    @abstractmethod
    def extract_skills(
        self,
        instruction: str,
        message: ChatMessage
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
    def __init__(self, model_name: str, config: Optional[ModelConfigOpenAI] = None):
        super().__init__(model_name, config)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=api_key)

    def chat(
        self, 
        chat_session: ChatSession,
        db_session: Session
    ) -> ChatMessage: 

        config = self.config.to_dict() if self.config else {}
        response = self.client.responses.create(
            model=self.model_name,
            input=chat_session.to_openai_input(),
            **config
        )
        
        # Create ChatMessage from OpenAI response
        assistant_message = ChatMessage.from_openai_message(chat_session, response)
        assistant_message.session_id = chat_session.session_id
        assistant_message.role = MessageType.ASSISTANT
        
        # Save to database
        db_session.add(assistant_message)
        db_session.commit()
        db_session.refresh(assistant_message)
        db_session.refresh(chat_session)  # Refresh to update chat_messages relationship
        
        return assistant_message

    def extract_skills(
        self,
        instruction: str,
        message: ChatMessage
    ) -> List[CustomSkill]:
        response = self.client.responses.parse(
            model=self.model_name,
            input=[
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": message.message_content,
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
    ) -> ChatSkillBase:
        
        mapping_prompt = get_prompt("information_mapper").format(skill=skill, available_skills=available_skills)
        
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
        response_dict = json.loads(response.output_text)
        
        logging.info(f"response_type: {type(response_dict)}")
        logging.info(f"response.output_text: {response_dict}")
        id = int(response_dict["id"])
        logging.info(f"id: {id} id_type: {type(id)}")
        skill = available_skills[id]

        if isinstance(skill, ESCOSkill):
            return ESCOSkillModel.from_pydantic(skill)
        else:
            raise NotImplementedError(f"Mapping for skill type {type(skill)} is not implemented")