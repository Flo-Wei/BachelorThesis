# Import order doesn't matter anymore with forward references
from Backend.database.models.users import User
from Backend.database.models.messages import ChatSession, ChatMessage, MessageType
from Backend.database.models.skills import ESCOSkill