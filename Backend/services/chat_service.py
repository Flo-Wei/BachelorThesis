"""
Chat service for managing conversational competency assessments.

This module provides the main service layer for handling chat-based competency
assessments, including conversation management, message processing, and integration
with conversation engines and LLM services.

Classes:
    ChatService: Main service for managing chat-based assessments
    ConversationEngine: Engine for processing conversations and extracting competencies
    LLMService: Service for interacting with Large Language Models
    CompetencyMappingService: Service for mapping discovered competencies to frameworks
    VisualizationService: Service for generating charts and reports
"""

from typing import List, Optional, Dict, Any, Protocol
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain.models import (
    User, Assessment, Conversation, Message, MappedCompetency, Skill, Evidence
)
from ..enums import (
    AssessmentStatus, ConversationState, MessageType, EvidenceType
)
from ..repositories.interfaces import (
    UserRepository, AssessmentRepository, SkillRepository
)
from ..frameworks.base import CompetencyFramework


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM providers."""
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text based on a prompt."""
        ...
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text."""
        ...


@dataclass
class PromptTemplate:
    """
    Template for LLM prompts with variable substitution.
    
    Attributes:
        template: The prompt template string with placeholders
        variables: Dictionary of variable names and their descriptions
        instructions: Additional instructions for the prompt
    """
    template: str
    variables: Dict[str, str]
    instructions: str = ""
    
    def format(self, **kwargs) -> str:
        """
        Format the template with provided variables.
        
        Args:
            **kwargs: Variable values to substitute in the template
            
        Returns:
            str: Formatted prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")


class QuestionStrategy(ABC):
    """
    Abstract base class for conversation question generation strategies.
    
    Different strategies can be implemented for various assessment modes,
    such as guided interviews, free-form conversations, or structured
    competency evaluations.
    """
    
    @abstractmethod
    def get_next_question(self, conversation: Conversation, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate the next question based on conversation state and context.
        
        Args:
            conversation: Current conversation state
            context: Additional context information
            
        Returns:
            Optional[str]: Next question to ask, or None if conversation should end
        """
        pass
    
    @abstractmethod
    def should_transition_state(self, conversation: Conversation) -> bool:
        """
        Determine if the conversation should transition to the next state.
        
        Args:
            conversation: Current conversation
            
        Returns:
            bool: True if state transition is needed, False otherwise
        """
        pass


class StateManager:
    """
    Manages conversation state transitions and validation.
    
    This class handles the logic for transitioning between different
    conversation states and ensuring valid state progressions.
    
    Attributes:
        _current_state: Current conversation state
        _state_history: History of state transitions
        _context: State-specific context information
    """
    
    def __init__(self):
        """Initialize the state manager."""
        self._current_state: Optional[ConversationState] = None
        self._state_history: List[ConversationState] = []
        self._context: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
    
    def initialize(self, conversation: Conversation) -> bool:
        """
        Initialize state management for a conversation.
        
        Args:
            conversation: Conversation to initialize
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            self._current_state = conversation.state
            self._state_history = [conversation.state]
            self._context = conversation.metadata.copy()
            return True
        except Exception as e:
            self._logger.error(f"Failed to initialize state manager: {str(e)}")
            return False
    
    def can_transition_to(self, target_state: ConversationState) -> bool:
        """
        Check if transition to target state is allowed.
        
        Args:
            target_state: State to transition to
            
        Returns:
            bool: True if transition is allowed, False otherwise
        """
        if not self._current_state:
            return target_state == ConversationState.INITIALIZING
        
        # Define allowed transitions
        transitions = {
            ConversationState.INITIALIZING: [ConversationState.MODE_SELECTION],
            ConversationState.MODE_SELECTION: [ConversationState.CONTEXT_GATHERING],
            ConversationState.CONTEXT_GATHERING: [ConversationState.COMPETENCY_DISCOVERY],
            ConversationState.COMPETENCY_DISCOVERY: [ConversationState.VALIDATION],
            ConversationState.VALIDATION: [ConversationState.MAPPING, ConversationState.COMPETENCY_DISCOVERY],
            ConversationState.MAPPING: [ConversationState.REVIEW],
            ConversationState.REVIEW: [ConversationState.COMPLETED],
            ConversationState.COMPLETED: []  # Terminal state
        }
        
        return target_state in transitions.get(self._current_state, [])
    
    def transition_to(self, target_state: ConversationState) -> bool:
        """
        Transition to a new state.
        
        Args:
            target_state: State to transition to
            
        Returns:
            bool: True if transition was successful, False otherwise
        """
        if not self.can_transition_to(target_state):
            self._logger.warning(f"Invalid state transition from {self._current_state} to {target_state}")
            return False
        
        try:
            self._state_history.append(target_state)
            self._current_state = target_state
            self._logger.info(f"State transitioned to {target_state}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to transition state: {str(e)}")
            return False
    
    def get_current_state(self) -> Optional[ConversationState]:
        """Get the current conversation state."""
        return self._current_state
    
    def get_state_history(self) -> List[ConversationState]:
        """Get the history of state transitions."""
        return self._state_history.copy()
    
    def update_context(self, updates: Dict[str, Any]) -> None:
        """Update the state context with new information."""
        self._context.update(updates)
    
    def get_context(self) -> Dict[str, Any]:
        """Get the current state context."""
        return self._context.copy()


class LLMService:
    """
    Service for interacting with Large Language Models.
    
    This service provides an abstraction layer over different LLM providers
    and handles prompt management, response processing, and entity extraction
    for competency assessment purposes.
    
    Attributes:
        _provider: LLM provider implementation
        _prompt_template: Template for generating prompts
        _logger: Logger for service operations
    """
    
    def __init__(self, provider: LLMProvider, prompt_template: Optional[PromptTemplate] = None):
        """
        Initialize the LLM service.
        
        Args:
            provider: LLM provider implementation
            prompt_template: Optional custom prompt template
        """
        self._provider = provider
        self._prompt_template = prompt_template or self._get_default_template()
        self._logger = logging.getLogger(__name__)
    
    def _get_default_template(self) -> PromptTemplate:
        """Get the default prompt template for competency assessment."""
        return PromptTemplate(
            template="""
You are an AI assistant helping to assess competencies through conversation.

Context: {context}
Previous conversation: {conversation_history}
Current phase: {current_phase}

User message: {user_message}

Please respond appropriately based on the current phase and continue the competency assessment conversation.
""",
            variables={
                "context": "Assessment context and background",
                "conversation_history": "Previous messages in the conversation",
                "current_phase": "Current assessment phase",
                "user_message": "Latest message from the user"
            },
            instructions="Generate helpful responses that guide the competency assessment process."
        )
    
    def generate_response(self, conversation: Conversation, user_message: str, 
                         context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate a response to a user message.
        
        Args:
            conversation: Current conversation
            user_message: Latest message from user
            context: Optional additional context
            
        Returns:
            Optional[str]: Generated response, or None if generation failed
        """
        try:
            # Prepare conversation history
            history = []
            for msg in conversation.messages[-5:]:  # Last 5 messages for context
                role = "User" if msg.type == MessageType.USER_MESSAGE else "Assistant"
                history.append(f"{role}: {msg.content}")
            
            conversation_history = "\n".join(history)
            
            # Format prompt
            prompt_vars = {
                "context": context or {},
                "conversation_history": conversation_history,
                "current_phase": conversation.current_phase,
                "user_message": user_message
            }
            
            prompt = self._prompt_template.format(**prompt_vars)
            
            # Generate response
            response = self._provider.generate_text(prompt)
            self._logger.info("Generated LLM response successfully")
            return response
            
        except Exception as e:
            self._logger.error(f"Failed to generate response: {str(e)}")
            return None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities (skills, competencies) from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[Dict[str, Any]]: List of extracted entities
        """
        try:
            return self._provider.extract_entities(text)
        except Exception as e:
            self._logger.error(f"Failed to extract entities: {str(e)}")
            return []
    
    def classify_intent(self, message: str) -> Optional[str]:
        """
        Classify the intent of a user message.
        
        Args:
            message: User message to classify
            
        Returns:
            Optional[str]: Classified intent, or None if classification failed
        """
        try:
            # Simple intent classification prompt
            prompt = f"""
Classify the intent of this message in a competency assessment context:

Message: "{message}"

Possible intents:
- skill_description: User is describing a skill or competency
- experience_sharing: User is sharing relevant experience
- question: User is asking a question
- confirmation: User is confirming or agreeing
- clarification: User is asking for clarification
- other: Other types of messages

Intent:"""
            
            response = self._provider.generate_text(prompt)
            intent = response.strip().lower()
            
            valid_intents = [
                "skill_description", "experience_sharing", "question", 
                "confirmation", "clarification", "other"
            ]
            
            return intent if intent in valid_intents else "other"
            
        except Exception as e:
            self._logger.error(f"Failed to classify intent: {str(e)}")
            return None
    
    def switch_provider(self, new_provider: LLMProvider) -> bool:
        """
        Switch to a different LLM provider.
        
        Args:
            new_provider: New LLM provider to use
            
        Returns:
            bool: True if switch was successful, False otherwise
        """
        try:
            self._provider = new_provider
            self._logger.info("Successfully switched LLM provider")
            return True
        except Exception as e:
            self._logger.error(f"Failed to switch provider: {str(e)}")
            return False


class ConversationEngine:
    """
    Engine for processing user input and managing conversation flow.
    
    This class orchestrates the conversation logic, processes user responses,
    generates appropriate questions, and extracts competency information
    from the dialogue.
    
    Attributes:
        _strategy: Question generation strategy
        _state_manager: State management component
        _logger: Logger for engine operations
    """
    
    def __init__(self, strategy: QuestionStrategy, state_manager: Optional[StateManager] = None):
        """
        Initialize the conversation engine.
        
        Args:
            strategy: Question generation strategy
            state_manager: Optional state manager (creates default if None)
        """
        self._strategy = strategy
        self._state_manager = state_manager or StateManager()
        self._logger = logging.getLogger(__name__)
    
    def process_user_input(self, conversation: Conversation, user_input: str) -> Dict[str, Any]:
        """
        Process user input and update conversation state.
        
        Args:
            conversation: Current conversation
            user_input: User's input message
            
        Returns:
            Dict[str, Any]: Processing results including extracted information
        """
        try:
            # Add user message to conversation
            user_message = Message(
                type=MessageType.USER_MESSAGE,
                content=user_input,
                sender="user",
                conversation_id=conversation.id
            )
            conversation.add_message(user_message)
            
            # Extract competency information
            competencies = self.extract_competencies(user_input)
            
            # Validate response appropriateness
            validation_result = self.validate_response(user_input, conversation.state)
            
            # Check if state transition is needed
            should_transition = self._strategy.should_transition_state(conversation)
            
            return {
                "message_added": True,
                "extracted_competencies": competencies,
                "validation_result": validation_result,
                "should_transition": should_transition,
                "processed_at": datetime.now(timezone.utc)
            }
            
        except Exception as e:
            self._logger.error(f"Failed to process user input: {str(e)}")
            return {"error": str(e), "message_added": False}
    
    def generate_next_question(self, conversation: Conversation, 
                             context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate the next question for the conversation.
        
        Args:
            conversation: Current conversation
            context: Optional additional context
            
        Returns:
            Optional[str]: Next question to ask, or None if conversation should end
        """
        try:
            return self._strategy.get_next_question(conversation, context or {})
        except Exception as e:
            self._logger.error(f"Failed to generate next question: {str(e)}")
            return None
    
    def extract_competencies(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract competency information from text.
        
        Args:
            text: Text to analyze for competencies
            
        Returns:
            List[Dict[str, Any]]: List of extracted competency information
        """
        try:
            # Simple keyword-based extraction (would be enhanced with NLP)
            competency_indicators = [
                "skill", "ability", "competency", "experience", "knowledge",
                "can do", "capable of", "good at", "experienced in", "trained in"
            ]
            
            text_lower = text.lower()
            extracted = []
            
            for indicator in competency_indicators:
                if indicator in text_lower:
                    # Extract context around the indicator
                    words = text.split()
                    for i, word in enumerate(words):
                        if indicator in word.lower():
                            # Get surrounding context
                            start = max(0, i - 3)
                            end = min(len(words), i + 4)
                            context = " ".join(words[start:end])
                            
                            extracted.append({
                                "indicator": indicator,
                                "context": context,
                                "position": i,
                                "confidence": 0.7  # Simple confidence score
                            })
            
            return extracted
            
        except Exception as e:
            self._logger.error(f"Failed to extract competencies: {str(e)}")
            return []
    
    def validate_response(self, response: str, current_state: ConversationState) -> Dict[str, Any]:
        """
        Validate if a response is appropriate for the current conversation state.
        
        Args:
            response: User response to validate
            current_state: Current conversation state
            
        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            # Basic validation logic
            is_valid = True
            issues = []
            
            # Check minimum length
            if len(response.strip()) < 5:
                is_valid = False
                issues.append("Response too short")
            
            # State-specific validation
            if current_state == ConversationState.COMPETENCY_DISCOVERY:
                # Look for competency-related content
                competency_keywords = ["skill", "experience", "able", "can", "know"]
                has_competency_content = any(keyword in response.lower() for keyword in competency_keywords)
                if not has_competency_content:
                    issues.append("Response lacks competency-related content")
            
            return {
                "is_valid": is_valid and len(issues) == 0,
                "issues": issues,
                "confidence": 0.8 if is_valid else 0.3
            }
            
        except Exception as e:
            self._logger.error(f"Failed to validate response: {str(e)}")
            return {"is_valid": False, "error": str(e)}


class CompetencyMappingService:
    """
    Service for mapping discovered competencies to framework standards.
    
    This service takes competencies identified during conversations and
    maps them to standardized competency frameworks like ESCO or
    organization-specific frameworks.
    
    Attributes:
        _framework_repo: Repository for accessing competency frameworks
        _algorithm: Mapping algorithm implementation
        _logger: Logger for service operations
    """
    
    def __init__(self, framework_repo: Dict[str, CompetencyFramework]):
        """
        Initialize the competency mapping service.
        
        Args:
            framework_repo: Dictionary of available competency frameworks
        """
        self._framework_repo = framework_repo
        self._logger = logging.getLogger(__name__)
    
    def map_to_framework(self, competency_description: str, framework_name: str,
                        confidence_threshold: float = 0.5) -> List[MappedCompetency]:
        """
        Map a competency description to framework standards.
        
        Args:
            competency_description: Description of the competency to map
            framework_name: Name of the target framework
            confidence_threshold: Minimum confidence score for mappings
            
        Returns:
            List[MappedCompetency]: List of mapped competencies above threshold
        """
        try:
            framework = self._framework_repo.get(framework_name)
            if not framework:
                self._logger.error(f"Framework not found: {framework_name}")
                return []
            
            # Search for similar competencies in the framework
            search_results = framework.search_by_keyword(competency_description, limit=10)
            
            mapped_competencies = []
            for competency in search_results:
                # Calculate similarity score (simplified)
                similarity = self._calculate_similarity(competency_description, competency.name, competency.description)
                
                if similarity >= confidence_threshold:
                    mapped_comp = MappedCompetency(
                        competency_id=competency.id,
                        competency_name=competency.name,
                        confidence_score=similarity,
                        framework_source=framework_name
                    )
                    mapped_competencies.append(mapped_comp)
            
            # Sort by confidence score
            mapped_competencies.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return mapped_competencies
            
        except Exception as e:
            self._logger.error(f"Failed to map to framework: {str(e)}")
            return []
    
    def _calculate_similarity(self, description: str, name: str, framework_description: str) -> float:
        """
        Calculate similarity between descriptions (simplified implementation).
        
        Args:
            description: User's competency description
            name: Framework competency name
            framework_description: Framework competency description
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            # Simple word overlap similarity
            desc_words = set(description.lower().split())
            name_words = set(name.lower().split())
            framework_words = set(framework_description.lower().split())
            
            all_framework_words = name_words.union(framework_words)
            
            if not desc_words or not all_framework_words:
                return 0.0
            
            common_words = desc_words.intersection(all_framework_words)
            total_words = desc_words.union(all_framework_words)
            
            return len(common_words) / len(total_words) if total_words else 0.0
            
        except Exception:
            return 0.0
    
    def find_similar_competencies(self, competency_id: str, framework_name: str,
                                similarity_threshold: float = 0.7) -> List[MappedCompetency]:
        """
        Find competencies similar to a given competency.
        
        Args:
            competency_id: Reference competency ID
            framework_name: Framework to search in
            similarity_threshold: Minimum similarity score
            
        Returns:
            List[MappedCompetency]: List of similar competencies
        """
        try:
            framework = self._framework_repo.get(framework_name)
            if not framework:
                return []
            
            similar_comps = framework.find_similar_competencies(
                competency_id, threshold=similarity_threshold
            )
            
            mapped_competencies = []
            for comp in similar_comps:
                mapped_comp = MappedCompetency(
                    competency_id=comp.id,
                    competency_name=comp.name,
                    confidence_score=similarity_threshold,  # Use threshold as base confidence
                    framework_source=framework_name
                )
                mapped_competencies.append(mapped_comp)
            
            return mapped_competencies
            
        except Exception as e:
            self._logger.error(f"Failed to find similar competencies: {str(e)}")
            return []
    
    def validate_mapping(self, mapped_competency: MappedCompetency) -> bool:
        """
        Validate a competency mapping.
        
        Args:
            mapped_competency: Mapped competency to validate
            
        Returns:
            bool: True if mapping is valid, False otherwise
        """
        try:
            framework = self._framework_repo.get(mapped_competency.framework_source)
            if not framework:
                return False
            
            # Check if competency exists in framework
            exists = framework.validate_competency_id(mapped_competency.competency_id)
            
            # Check confidence score is reasonable
            confidence_valid = 0.0 <= mapped_competency.confidence_score <= 1.0
            
            return exists and confidence_valid
            
        except Exception:
            return False
    
    def suggest_competencies(self, context: Dict[str, Any], framework_name: str,
                           limit: int = 5) -> List[MappedCompetency]:
        """
        Suggest relevant competencies based on context.
        
        Args:
            context: Context information (e.g., job role, experience area)
            framework_name: Framework to suggest from
            limit: Maximum number of suggestions
            
        Returns:
            List[MappedCompetency]: List of suggested competencies
        """
        try:
            framework = self._framework_repo.get(framework_name)
            if not framework:
                return []
            
            suggestions = []
            
            # Extract keywords from context
            keywords = []
            for key, value in context.items():
                if isinstance(value, str):
                    keywords.extend(value.lower().split())
            
            # Search for competencies matching context keywords
            for keyword in keywords[:3]:  # Use top 3 keywords
                results = framework.search_by_keyword(keyword, limit=3)
                for comp in results:
                    mapped_comp = MappedCompetency(
                        competency_id=comp.id,
                        competency_name=comp.name,
                        confidence_score=0.6,  # Default suggestion confidence
                        framework_source=framework_name
                    )
                    suggestions.append(mapped_comp)
            
            # Remove duplicates and limit results
            unique_suggestions = []
            seen_ids = set()
            for suggestion in suggestions:
                if suggestion.competency_id not in seen_ids:
                    unique_suggestions.append(suggestion)
                    seen_ids.add(suggestion.competency_id)
                if len(unique_suggestions) >= limit:
                    break
            
            return unique_suggestions
            
        except Exception as e:
            self._logger.error(f"Failed to suggest competencies: {str(e)}")
            return []


class VisualizationService:
    """
    Service for generating visualizations and reports.
    
    This service creates various types of visual representations of
    competency data, including charts, reports, and export formats
    for assessment results and skill profiles.
    
    Attributes:
        _logger: Logger for service operations
    """
    
    def __init__(self):
        """Initialize the visualization service."""
        self._logger = logging.getLogger(__name__)
    
    def generate_radar_chart(self, skills: List[Skill], categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a radar chart representation of skills.
        
        Args:
            skills: List of skills to visualize
            categories: Optional list of categories to include
            
        Returns:
            Dict[str, Any]: Radar chart data structure
        """
        try:
            # Group skills by category
            skill_groups = {}
            for skill in skills:
                category = skill.framework_source or "Other"
                if categories and category not in categories:
                    continue
                
                if category not in skill_groups:
                    skill_groups[category] = []
                skill_groups[category].append(skill)
            
            # Calculate average proficiency per category
            chart_data = {
                "categories": [],
                "values": [],
                "max_value": 4,  # Expert level
                "title": "Skills Radar Chart"
            }
            
            for category, category_skills in skill_groups.items():
                avg_proficiency = sum(skill.level.numeric_value for skill in category_skills) / len(category_skills)
                chart_data["categories"].append(category)
                chart_data["values"].append(avg_proficiency)
            
            return chart_data
            
        except Exception as e:
            self._logger.error(f"Failed to generate radar chart: {str(e)}")
            return {"error": str(e)}
    
    def generate_skill_tree(self, skills: List[Skill]) -> Dict[str, Any]:
        """
        Generate a skill tree visualization.
        
        Args:
            skills: List of skills to visualize
            
        Returns:
            Dict[str, Any]: Skill tree data structure
        """
        try:
            # Organize skills hierarchically
            tree_data = {
                "name": "Skills",
                "children": []
            }
            
            # Group by framework source
            frameworks = {}
            for skill in skills:
                framework = skill.framework_source or "Other"
                if framework not in frameworks:
                    frameworks[framework] = []
                frameworks[framework].append(skill)
            
            for framework_name, framework_skills in frameworks.items():
                framework_node = {
                    "name": framework_name,
                    "children": []
                }
                
                for skill in framework_skills:
                    skill_node = {
                        "name": skill.name,
                        "level": skill.level.value,
                        "evidence_count": len(skill.evidences),
                        "size": skill.level.numeric_value * 10  # Size based on proficiency
                    }
                    framework_node["children"].append(skill_node)
                
                tree_data["children"].append(framework_node)
            
            return tree_data
            
        except Exception as e:
            self._logger.error(f"Failed to generate skill tree: {str(e)}")
            return {"error": str(e)}
    
    def generate_progress_report(self, assessment: Assessment) -> Dict[str, Any]:
        """
        Generate a progress report for an assessment.
        
        Args:
            assessment: Assessment to generate report for
            
        Returns:
            Dict[str, Any]: Progress report data
        """
        try:
            report_data = {
                "assessment_id": assessment.id,
                "status": assessment.status.value,
                "progress_percentage": self._calculate_progress(assessment),
                "competencies_mapped": len(assessment.mapped_competencies),
                "conversation_summary": {
                    "total_messages": len(assessment.conversation.messages) if assessment.conversation else 0,
                    "user_messages": len([m for m in assessment.conversation.messages 
                                        if m.type == MessageType.USER_MESSAGE]) if assessment.conversation else 0,
                    "current_state": assessment.conversation.state.value if assessment.conversation else None
                },
                "high_confidence_mappings": len([
                    comp for comp in assessment.mapped_competencies 
                    if comp.is_high_confidence
                ]),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            return report_data
            
        except Exception as e:
            self._logger.error(f"Failed to generate progress report: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_progress(self, assessment: Assessment) -> float:
        """
        Calculate the progress percentage for an assessment.
        
        Args:
            assessment: Assessment to calculate progress for
            
        Returns:
            float: Progress percentage (0.0 to 100.0)
        """
        try:
            if assessment.status == AssessmentStatus.NOT_STARTED:
                return 0.0
            elif assessment.status == AssessmentStatus.COMPLETED:
                return 100.0
            else:
                # Calculate based on conversation state
                if not assessment.conversation:
                    return 10.0
                
                state_progress = {
                    ConversationState.INITIALIZING: 10.0,
                    ConversationState.MODE_SELECTION: 20.0,
                    ConversationState.CONTEXT_GATHERING: 35.0,
                    ConversationState.COMPETENCY_DISCOVERY: 60.0,
                    ConversationState.VALIDATION: 75.0,
                    ConversationState.MAPPING: 85.0,
                    ConversationState.REVIEW: 95.0,
                    ConversationState.COMPLETED: 100.0
                }
                
                return state_progress.get(assessment.conversation.state, 50.0)
                
        except Exception:
            return 0.0
    
    def export_to_pdf(self, data: Dict[str, Any], template: str = "default") -> bytes:
        """
        Export data to PDF format.
        
        Args:
            data: Data to export
            template: Template to use for PDF generation
            
        Returns:
            bytes: PDF file content
        """
        # This would integrate with a PDF generation library
        # For now, return a placeholder
        self._logger.info(f"PDF export requested with template: {template}")
        return b"PDF content placeholder"
    
    def export_to_json(self, data: Dict[str, Any]) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Data to export
            
        Returns:
            str: JSON string representation
        """
        try:
            import json
            return json.dumps(data, indent=2, default=str)
        except Exception as e:
            self._logger.error(f"Failed to export to JSON: {str(e)}")
            return "{}"


class ChatService:
    """
    Main chat service for managing conversational competency assessments.
    
    This service orchestrates the entire chat-based assessment process,
    integrating conversation management, LLM interaction, competency mapping,
    and data persistence.
    
    Attributes:
        _engine: Conversation engine for processing interactions
        _llm_service: LLM service for generating responses
        _mapping_service: Service for mapping competencies to frameworks
        _user_repo: Repository for user data operations
        _assessment_repo: Repository for assessment data operations
        _logger: Logger for service operations
    """
    
    def __init__(self, engine: ConversationEngine, llm_service: LLMService,
                 mapping_service: CompetencyMappingService,
                 user_repo: UserRepository, assessment_repo: AssessmentRepository):
        """
        Initialize the chat service.
        
        Args:
            engine: Conversation engine
            llm_service: LLM service
            mapping_service: Competency mapping service
            user_repo: User repository
            assessment_repo: Assessment repository
        """
        self._engine = engine
        self._llm_service = llm_service
        self._mapping_service = mapping_service
        self._user_repo = user_repo
        self._assessment_repo = assessment_repo
        self._logger = logging.getLogger(__name__)
    
    def start_conversation(self, user_id: str, framework_name: Optional[str] = None) -> Optional[Assessment]:
        """
        Start a new conversational assessment.
        
        Args:
            user_id: ID of the user starting the assessment
            framework_name: Optional competency framework to use
            
        Returns:
            Optional[Assessment]: New assessment if successful, None otherwise
        """
        try:
            # Verify user exists
            user = self._user_repo.find_by_id(user_id)
            if not user:
                self._logger.error(f"User not found: {user_id}")
                return None
            
            # Create new assessment
            assessment = Assessment(user_id=user_id)
            
            # Start the assessment
            if not assessment.start():
                self._logger.error("Failed to start assessment")
                return None
            
            # Save assessment
            if not self._assessment_repo.save(assessment):
                self._logger.error("Failed to save assessment")
                return None
            
            # Add to user's assessments
            user.add_assessment(assessment)
            self._user_repo.update(user)
            
            self._logger.info(f"Started conversation for user {user_id}")
            return assessment
            
        except Exception as e:
            self._logger.error(f"Failed to start conversation: {str(e)}")
            return None
    
    def send_message(self, assessment_id: str, message_content: str) -> Optional[str]:
        """
        Send a message in an ongoing conversation.
        
        Args:
            assessment_id: ID of the assessment/conversation
            message_content: Content of the user's message
            
        Returns:
            Optional[str]: Bot response if successful, None otherwise
        """
        try:
            # Get assessment
            assessment = self._assessment_repo.find_by_id(assessment_id)
            if not assessment or not assessment.conversation:
                self._logger.error(f"Assessment or conversation not found: {assessment_id}")
                return None
            
            conversation = assessment.conversation
            
            # Process user input
            processing_result = self._engine.process_user_input(conversation, message_content)
            
            if not processing_result.get("message_added"):
                self._logger.error("Failed to process user input")
                return None
            
            # Generate bot response
            bot_response = self._llm_service.generate_response(conversation, message_content)
            
            if bot_response:
                # Add bot message to conversation
                bot_message = Message(
                    type=MessageType.BOT_MESSAGE,
                    content=bot_response,
                    sender="assistant",
                    conversation_id=conversation.id
                )
                conversation.add_message(bot_message)
            
            # Handle state transitions if needed
            if processing_result.get("should_transition"):
                conversation.transition_to_next_state()
            
            # Extract and map competencies
            extracted_competencies = processing_result.get("extracted_competencies", [])
            for comp_info in extracted_competencies:
                # Create evidence from conversation
                evidence = Evidence(
                    description=f"Extracted from conversation: {comp_info['context']}",
                    type=EvidenceType.CONVERSATION_EXTRACT,
                    extracted_text=comp_info['context'],
                    conversation_id=conversation.id
                )
                
                # Map to framework if available
                if assessment.framework:
                    mappings = self._mapping_service.map_to_framework(
                        comp_info['context'], 
                        assessment.framework.get_name()
                    )
                    for mapping in mappings:
                        mapping.add_supporting_evidence(evidence.id)
                        assessment.add_mapped_competency(mapping)
            
            # Save updated assessment
            self._assessment_repo.update(assessment)
            
            return bot_response
            
        except Exception as e:
            self._logger.error(f"Failed to send message: {str(e)}")
            return None
    
    def end_conversation(self, assessment_id: str) -> bool:
        """
        End an ongoing conversation.
        
        Args:
            assessment_id: ID of the assessment to end
            
        Returns:
            bool: True if conversation was ended successfully, False otherwise
        """
        try:
            assessment = self._assessment_repo.find_by_id(assessment_id)
            if not assessment:
                return False
            
            # Complete the assessment
            success = assessment.complete()
            
            if success:
                # Save final state
                self._assessment_repo.update(assessment)
                self._logger.info(f"Ended conversation for assessment {assessment_id}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to end conversation: {str(e)}")
            return False
    
    def get_conversation_history(self, assessment_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get the conversation history for an assessment.
        
        Args:
            assessment_id: ID of the assessment
            
        Returns:
            Optional[List[Dict[str, Any]]]: Conversation history if found, None otherwise
        """
        try:
            assessment = self._assessment_repo.find_by_id(assessment_id)
            if not assessment or not assessment.conversation:
                return None
            
            history = []
            for message in assessment.conversation.messages:
                history.append({
                    "id": message.id,
                    "type": message.type.value,
                    "content": message.content,
                    "sender": message.sender,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata
                })
            
            return history
            
        except Exception as e:
            self._logger.error(f"Failed to get conversation history: {str(e)}")
            return None 