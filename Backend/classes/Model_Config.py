from pydantic import BaseModel, Field
from typing import Optional, Literal

class ModelConfig(BaseModel):
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Controls randomness of the model output")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum number of tokens to generate")
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0, description="Controls diversity via nucleus sampling")
    # frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Reduces repetition of frequent tokens")
    # presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Reduces repetition of any tokens")
    stop: Optional[list[str]] = Field(default=None, description="Stop generation when these strings are encountered")
    
    def to_dict(self) -> dict:
        params = self.model_dump(exclude_none=True)
        return params
    

class ModelConfigOpenAI(ModelConfig):
    response_format: Optional[Literal["text", "json_object"]] = Field(
        default=None, 
        description="Specify response format for structured outputs"
    )
    seed: Optional[int] = Field(
        default=None, 
        description="Random seed for reproducible outputs"
    )
    tools: Optional[list[dict]] = Field(
        default=None, 
        description="List of tools/functions the model can call"
    )
    tool_choice: Optional[Literal["none", "auto", "required"]] = Field(
        default=None, 
        description="Controls how the model responds to tool calls"
    )
    user: Optional[str] = Field(
        default=None, 
        description="Unique identifier for end-user (for abuse monitoring)"
    )
    logit_bias: Optional[dict[int, float]] = Field(
        default=None, 
        description="Modify likelihood of specific tokens appearing"
    )
    logprobs: Optional[bool] = Field(
        default=False, 
        description="Include log probabilities in response"
    )
    top_logprobs: Optional[int] = Field(
        default=None, 
        ge=0, 
        le=20, 
        description="Number of log probabilities to return"
    )

    