"""
Freiwilligenpass (Volunteer Pass) framework implementation.

This module provides a concrete implementation of the CompetencyFramework interface
for the Freiwilligenpass framework, which is designed to recognize and validate
competencies acquired through voluntary work and civic engagement.

Classes:
    FreiwilligenpassFramework: Implementation of Freiwilligenpass competency framework
    FPCompetency: Freiwilligenpass-specific competency data structure
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import logging

from .base import CompetencyFramework, Competency, FrameworkError, FrameworkNotLoadedException


@dataclass
class FPCompetency(Competency):
    """
    Freiwilligenpass-specific competency with additional metadata.
    
    Extends the base Competency class with Freiwilligenpass-specific attributes
    and functionality for handling competencies in the volunteering context.
    
    Additional Attributes:
        competency_area: Main area of competency (e.g., "Social", "Organizational")
        sub_area: Specific sub-area within the main competency area
        complexity_level: Complexity level of the competency (Basic, Intermediate, Advanced)
        volunteer_context: Typical volunteering contexts where this competency is relevant
        learning_outcomes: Specific learning outcomes associated with this competency
        assessment_methods: Suggested methods for assessing this competency
        recognition_criteria: Criteria for recognizing this competency
    """
    
    competency_area: str = ""
    sub_area: str = ""
    complexity_level: str = ""
    volunteer_context: List[str] = field(default_factory=list)
    learning_outcomes: List[str] = field(default_factory=list)
    assessment_methods: List[str] = field(default_factory=list)
    recognition_criteria: List[str] = field(default_factory=list)
    
    def is_basic_level(self) -> bool:
        """Check if this is a basic level competency."""
        return self.complexity_level.lower() == "basic"
    
    def is_intermediate_level(self) -> bool:
        """Check if this is an intermediate level competency."""
        return self.complexity_level.lower() == "intermediate"
    
    def is_advanced_level(self) -> bool:
        """Check if this is an advanced level competency."""
        return self.complexity_level.lower() == "advanced"
    
    def get_full_area_path(self) -> str:
        """
        Get the full path of competency area and sub-area.
        
        Returns:
            str: Full path like "Social > Community Engagement"
        """
        if self.sub_area:
            return f"{self.competency_area} > {self.sub_area}"
        return self.competency_area
    
    def applies_to_context(self, context: str) -> bool:
        """
        Check if this competency applies to a specific volunteer context.
        
        Args:
            context: Volunteer context to check
            
        Returns:
            bool: True if competency applies to the context, False otherwise
        """
        return context.lower() in [ctx.lower() for ctx in self.volunteer_context]


class FreiwilligenpassFramework(CompetencyFramework):
    """
    Freiwilligenpass (Volunteer Pass) framework implementation.
    
    This class provides access to the Freiwilligenpass framework, which is designed
    to recognize, document, and validate competencies acquired through voluntary
    work and civic engagement. The framework focuses on both professional skills
    and personal development competencies gained through volunteering experiences.
    
    The framework is particularly valuable for making visible the often overlooked
    learning and skill development that occurs in volunteer settings, providing
    structured recognition for informal and non-formal learning.
    
    Attributes:
        _competencies: Internal cache of loaded competencies
        _competency_map: Index for fast competency lookup by ID
        _categories: Set of available categories/areas
        _complexity_levels: Available complexity levels
        _is_loaded: Flag indicating if framework data is loaded
        _data_source: Path or URL to framework data source
    """
    
    def __init__(self, data_source: Optional[str] = None):
        """
        Initialize the Freiwilligenpass framework.
        
        Args:
            data_source: Optional path to framework data file or URL
        """
        self._competencies: List[FPCompetency] = []
        self._competency_map: Dict[str, FPCompetency] = {}
        self._categories: Set[str] = set()
        self._competency_areas: Dict[str, List[FPCompetency]] = {}
        self._complexity_levels: Set[str] = set()
        self._volunteer_contexts: Set[str] = set()
        self._is_loaded: bool = False
        self._data_source: Optional[str] = data_source
        self._logger = logging.getLogger(__name__)
        
        # Framework metadata
        self._name = "Freiwilligenpass"
        self._version = "2.0"
        self._description = ("Framework for recognizing and validating competencies "
                           "acquired through voluntary work and civic engagement.")
    
    def get_name(self) -> str:
        """Get the name of the Freiwilligenpass framework."""
        return self._name
    
    def get_version(self) -> str:
        """Get the version of the Freiwilligenpass framework."""
        return self._version
    
    def get_description(self) -> str:
        """Get the description of the Freiwilligenpass framework."""
        return self._description
    
    def load_framework(self, data_source: Optional[str] = None) -> bool:
        """
        Load Freiwilligenpass competency data from the specified source.
        
        Args:
            data_source: Optional path to framework data file or URL
            
        Returns:
            bool: True if loading was successful, False otherwise
            
        Raises:
            FrameworkError: If there's an error loading the framework data
        """
        try:
            source = data_source or self._data_source
            if not source:
                # Load sample/mock data if no source specified
                self._load_sample_data()
            else:
                self._load_from_source(source)
            
            self._build_indices()
            self._is_loaded = True
            self._logger.info(f"Freiwilligenpass framework loaded successfully with {len(self._competencies)} competencies")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to load Freiwilligenpass framework: {str(e)}")
            raise FrameworkError(f"Failed to load Freiwilligenpass framework: {str(e)}", self._name, e)
    
    def _load_sample_data(self) -> None:
        """Load sample Freiwilligenpass competencies for demonstration purposes."""
        sample_competencies = [
            FPCompetency(
                id="FP001",
                name="Event Organization",
                description="Plan, coordinate and execute events for volunteer organizations",
                framework_id="fp_event_org_001",
                category="Organizational Competencies",
                competency_area="Organizational",
                sub_area="Event Management",
                complexity_level="Intermediate",
                volunteer_context=["Community Events", "Fundraising", "Awareness Campaigns"],
                learning_outcomes=[
                    "Plan event timelines and logistics",
                    "Coordinate with multiple stakeholders",
                    "Manage event budget and resources",
                    "Handle unexpected situations during events"
                ],
                assessment_methods=["Portfolio review", "Supervisor feedback", "Event documentation"],
                recognition_criteria=["Successfully organized at least 3 events", "Demonstrated planning skills"],
                keywords={"event", "organization", "planning", "coordination", "management"}
            ),
            FPCompetency(
                id="FP002",
                name="Community Engagement",
                description="Build relationships and engage with community members effectively",
                framework_id="fp_community_eng_002",
                category="Social Competencies",
                competency_area="Social",
                sub_area="Community Relations",
                complexity_level="Basic",
                volunteer_context=["Community Outreach", "Social Services", "Local Government"],
                learning_outcomes=[
                    "Communicate effectively with diverse community groups",
                    "Build trust and rapport with community members",
                    "Identify community needs and concerns",
                    "Facilitate community participation"
                ],
                assessment_methods=["Observation", "Community feedback", "Self-reflection"],
                recognition_criteria=["Regular community interaction", "Positive community feedback"],
                keywords={"community", "engagement", "communication", "outreach", "relationships"}
            ),
            FPCompetency(
                id="FP003",
                name="Team Leadership",
                description="Lead and motivate volunteer teams towards common goals",
                framework_id="fp_team_lead_003",
                category="Leadership Competencies",
                competency_area="Leadership",
                sub_area="Team Management",
                complexity_level="Advanced",
                volunteer_context=["Volunteer Teams", "Project Groups", "Committee Leadership"],
                learning_outcomes=[
                    "Motivate and inspire team members",
                    "Delegate tasks effectively",
                    "Resolve conflicts within teams",
                    "Set clear goals and expectations"
                ],
                assessment_methods=["360-degree feedback", "Leadership portfolio", "Team performance metrics"],
                recognition_criteria=["Led teams for minimum 6 months", "Achieved team objectives"],
                keywords={"leadership", "team", "motivation", "delegation", "management"}
            ),
            FPCompetency(
                id="FP004",
                name="Cultural Sensitivity",
                description="Work effectively with people from diverse cultural backgrounds",
                framework_id="fp_cultural_sens_004",
                category="Intercultural Competencies",
                competency_area="Social",
                sub_area="Cultural Awareness",
                complexity_level="Intermediate",
                volunteer_context=["Multicultural Programs", "Refugee Support", "International Cooperation"],
                learning_outcomes=[
                    "Demonstrate cultural awareness and sensitivity",
                    "Adapt communication styles to different cultures",
                    "Address cultural barriers effectively",
                    "Promote inclusive environments"
                ],
                assessment_methods=["Cultural competency assessment", "Peer feedback", "Case studies"],
                recognition_criteria=["Worked with diverse groups", "Demonstrated cultural awareness"],
                keywords={"cultural", "diversity", "sensitivity", "inclusion", "intercultural"}
            ),
            FPCompetency(
                id="FP005",
                name="Fundraising",
                description="Develop and implement strategies to raise funds for causes",
                framework_id="fp_fundraising_005",
                category="Organizational Competencies",
                competency_area="Organizational",
                sub_area="Resource Development",
                complexity_level="Advanced",
                volunteer_context=["Non-profit Organizations", "Charitable Causes", "Community Projects"],
                learning_outcomes=[
                    "Develop fundraising strategies",
                    "Write grant applications",
                    "Organize fundraising events",
                    "Build donor relationships"
                ],
                assessment_methods=["Fundraising results", "Portfolio review", "Donor feedback"],
                recognition_criteria=["Successfully raised funds", "Demonstrated fundraising skills"],
                keywords={"fundraising", "grants", "donors", "resources", "finance"}
            ),
            FPCompetency(
                id="FP006",
                name="Crisis Response",
                description="Respond effectively to emergency situations and crises",
                framework_id="fp_crisis_resp_006",
                category="Emergency Competencies",
                competency_area="Operational",
                sub_area="Emergency Response",
                complexity_level="Advanced",
                volunteer_context=["Emergency Services", "Disaster Relief", "Crisis Support"],
                learning_outcomes=[
                    "Assess emergency situations quickly",
                    "Coordinate crisis response efforts",
                    "Provide emotional support during crises",
                    "Follow emergency protocols"
                ],
                assessment_methods=["Simulation exercises", "Emergency response records", "Training certificates"],
                recognition_criteria=["Emergency response training", "Crisis situation experience"],
                keywords={"crisis", "emergency", "response", "disaster", "support"}
            ),
            FPCompetency(
                id="FP007",
                name="Mentoring and Coaching",
                description="Guide and support the development of others through mentoring",
                framework_id="fp_mentoring_007",
                category="Educational Competencies",
                competency_area="Educational",
                sub_area="Personal Development",
                complexity_level="Intermediate",
                volunteer_context=["Youth Programs", "Skill Development", "Career Guidance"],
                learning_outcomes=[
                    "Establish effective mentoring relationships",
                    "Provide constructive feedback",
                    "Set development goals with mentees",
                    "Support personal growth and learning"
                ],
                assessment_methods=["Mentee feedback", "Mentoring portfolio", "Self-assessment"],
                recognition_criteria=["Mentored individuals successfully", "Demonstrated coaching skills"],
                keywords={"mentoring", "coaching", "guidance", "development", "support"}
            )
        ]
        
        self._competencies = sample_competencies
    
    def _load_from_source(self, source: str) -> None:
        """
        Load Freiwilligenpass data from file or URL source.
        
        Args:
            source: Path to data file or URL
        """
        # This would implement actual framework data loading
        # For now, we'll use the sample data
        self._load_sample_data()
        self._logger.info(f"Loaded Freiwilligenpass data from source: {source}")
    
    def _build_indices(self) -> None:
        """Build internal indices for fast lookup."""
        self._competency_map.clear()
        self._categories.clear()
        self._competency_areas.clear()
        self._complexity_levels.clear()
        self._volunteer_contexts.clear()
        
        for competency in self._competencies:
            # Build ID map
            self._competency_map[competency.id] = competency
            
            # Build categories set
            if competency.category:
                self._categories.add(competency.category)
            
            # Build competency areas index
            if competency.competency_area:
                if competency.competency_area not in self._competency_areas:
                    self._competency_areas[competency.competency_area] = []
                self._competency_areas[competency.competency_area].append(competency)
            
            # Build complexity levels set
            if competency.complexity_level:
                self._complexity_levels.add(competency.complexity_level)
            
            # Build volunteer contexts set
            for context in competency.volunteer_context:
                self._volunteer_contexts.add(context)
    
    def get_competencies(self) -> List[Competency]:
        """Get all competencies in the Freiwilligenpass framework."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return self._competencies.copy()
    
    def find_by_id(self, competency_id: str) -> Optional[Competency]:
        """Find a Freiwilligenpass competency by its ID."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return self._competency_map.get(competency_id)
    
    def search_by_keyword(self, keyword: str, limit: Optional[int] = None) -> List[Competency]:
        """Search Freiwilligenpass competencies by keyword."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        if not keyword:
            return []
        
        results = []
        keyword_lower = keyword.lower().strip()
        
        for competency in self._competencies:
            # Check if competency matches the keyword
            if competency.matches_keyword(keyword_lower):
                results.append(competency)
            # Also check learning outcomes and volunteer contexts
            elif isinstance(competency, FPCompetency):
                # Check learning outcomes
                for outcome in competency.learning_outcomes:
                    if keyword_lower in outcome.lower():
                        results.append(competency)
                        break
                else:
                    # Check volunteer contexts
                    for context in competency.volunteer_context:
                        if keyword_lower in context.lower():
                            results.append(competency)
                            break
        
        # Sort by relevance
        def relevance_score(comp: Competency) -> int:
            score = 0
            if keyword_lower == comp.name.lower():
                score += 100
            elif keyword_lower in comp.name.lower():
                score += 50
            elif keyword_lower in comp.description.lower():
                score += 25
            else:
                score += 10
            return score
        
        results.sort(key=relevance_score, reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    def get_categories(self) -> List[str]:
        """Get all available categories in Freiwilligenpass."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._categories))
    
    def get_competencies_by_category(self, category: str) -> List[Competency]:
        """Get all Freiwilligenpass competencies in a specific category."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return [comp for comp in self._competencies if comp.category == category]
    
    def get_competency_areas(self) -> List[str]:
        """
        Get all competency areas in Freiwilligenpass.
        
        Returns:
            List[str]: List of competency area names
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._competency_areas.keys()))
    
    def get_competencies_by_area(self, area: str) -> List[FPCompetency]:
        """
        Get all competencies in a specific competency area.
        
        Args:
            area: Name of the competency area
            
        Returns:
            List[FPCompetency]: List of competencies in the area
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return self._competency_areas.get(area, [])
    
    def get_complexity_levels(self) -> List[str]:
        """
        Get all complexity levels available in the framework.
        
        Returns:
            List[str]: List of complexity level names
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._complexity_levels))
    
    def get_competencies_by_complexity(self, level: str) -> List[FPCompetency]:
        """
        Get all competencies at a specific complexity level.
        
        Args:
            level: Complexity level to filter by
            
        Returns:
            List[FPCompetency]: List of competencies at the specified level
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return [comp for comp in self._competencies 
                if isinstance(comp, FPCompetency) and comp.complexity_level == level]
    
    def get_volunteer_contexts(self) -> List[str]:
        """
        Get all volunteer contexts mentioned in the framework.
        
        Returns:
            List[str]: List of volunteer context names
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._volunteer_contexts))
    
    def get_competencies_by_context(self, context: str) -> List[FPCompetency]:
        """
        Get all competencies relevant to a specific volunteer context.
        
        Args:
            context: Volunteer context to filter by
            
        Returns:
            List[FPCompetency]: List of competencies relevant to the context
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return [comp for comp in self._competencies 
                if isinstance(comp, FPCompetency) and comp.applies_to_context(context)]
    
    def find_similar_competencies(self, competency_id: str, 
                                threshold: float = 0.5,
                                limit: Optional[int] = None) -> List[Competency]:
        """Find Freiwilligenpass competencies similar to a given competency."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        reference_competency = self.find_by_id(competency_id)
        if not reference_competency:
            return []
        
        similar_competencies = []
        
        for competency in self._competencies:
            if competency.id == competency_id:
                continue
            
            similarity = reference_competency.get_similarity_score(competency)
            if similarity >= threshold:
                similar_competencies.append((competency, similarity))
        
        # Sort by similarity score (highest first)
        similar_competencies.sort(key=lambda x: x[1], reverse=True)
        
        # Extract just the competencies
        results = [comp for comp, _ in similar_competencies]
        
        if limit:
            results = results[:limit]
        
        return results
    
    def is_loaded(self) -> bool:
        """Check if the Freiwilligenpass framework is loaded."""
        return self._is_loaded
    
    def reload(self) -> bool:
        """Reload the Freiwilligenpass framework data."""
        try:
            self._is_loaded = False
            return self.load_framework()
        except Exception as e:
            self._logger.error(f"Failed to reload Freiwilligenpass framework: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical information about the Freiwilligenpass framework."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        # Count competencies by complexity level
        complexity_counts = {}
        for competency in self._competencies:
            if isinstance(competency, FPCompetency):
                level = competency.complexity_level or "unknown"
                complexity_counts[level] = complexity_counts.get(level, 0) + 1
        
        # Count competencies by area
        area_counts = {}
        for competency in self._competencies:
            if isinstance(competency, FPCompetency):
                area = competency.competency_area or "unknown"
                area_counts[area] = area_counts.get(area, 0) + 1
        
        return {
            "framework_name": self._name,
            "framework_version": self._version,
            "total_competencies": len(self._competencies),
            "categories": len(self._categories),
            "competency_areas": len(self._competency_areas),
            "complexity_levels": len(self._complexity_levels),
            "volunteer_contexts": len(self._volunteer_contexts),
            "competencies_by_complexity": complexity_counts,
            "competencies_by_area": area_counts,
            "is_loaded": self._is_loaded,
            "data_source": self._data_source
        } 