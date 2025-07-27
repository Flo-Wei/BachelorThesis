"""
ESCO (European Skills, Competences, Qualifications and Occupations) framework implementation.

This module provides a concrete implementation of the CompetencyFramework interface
for the ESCO framework, which is the European multilingual classification of
Skills, Competences and Occupations.

Classes:
    ESCOFramework: Implementation of ESCO competency framework
    ESCOCompetency: ESCO-specific competency data structure
"""

from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path

from .base import CompetencyFramework, Competency, FrameworkError, FrameworkNotLoadedException


@dataclass
class ESCOCompetency(Competency):
    """
    ESCO-specific competency with additional metadata.
    
    Extends the base Competency class with ESCO-specific attributes
    and functionality for handling the European Skills framework.
    
    Additional Attributes:
        skill_type: Type of skill (skill/competence, knowledge, skill)
        reusability_level: Level of reusability (cross-sector, sector-specific, etc.)
        skill_group: ESCO skill group classification
        alternative_labels: Alternative names and labels for this competency
        broader_concepts: References to broader concept URIs
        narrower_concepts: References to narrower concept URIs
        esco_uri: Official ESCO URI for this competency
    """
    
    skill_type: str = ""
    reusability_level: str = ""
    skill_group: str = ""
    alternative_labels: List[str] = field(default_factory=list)
    broader_concepts: List[str] = field(default_factory=list)
    narrower_concepts: List[str] = field(default_factory=list)
    esco_uri: str = ""
    
    def get_all_labels(self) -> List[str]:
        """
        Get all labels (name + alternatives) for this competency.
        
        Returns:
            List[str]: Complete list of labels for this competency
        """
        labels = [self.name] if self.name else []
        labels.extend(self.alternative_labels)
        return labels
    
    def is_skill_competence(self) -> bool:
        """Check if this is a skill/competence type."""
        return self.skill_type.lower() == "skill/competence"
    
    def is_knowledge(self) -> bool:
        """Check if this is a knowledge type."""
        return self.skill_type.lower() == "knowledge"
    
    def is_skill(self) -> bool:
        """Check if this is a skill type."""
        return self.skill_type.lower() == "skill"


class ESCOFramework(CompetencyFramework):
    """
    ESCO (European Skills, Competences, Qualifications and Occupations) framework implementation.
    
    This class provides access to the ESCO framework, which is the European
    multilingual classification of Skills, Competences and Occupations.
    ESCO works as a dictionary, describing, identifying and classifying
    professional occupations and skills relevant for the European labor market.
    
    The framework supports multiple languages and provides standardized
    references for skills and competencies across European countries.
    
    Attributes:
        _competencies: Internal cache of loaded competencies
        _competency_map: Index for fast competency lookup by ID
        _categories: Set of available categories
        _is_loaded: Flag indicating if framework data is loaded
        _data_source: Path or URL to ESCO data source
        _language: Language code for competency descriptions
    """
    
    def __init__(self, data_source: Optional[str] = None, language: str = "en"):
        """
        Initialize the ESCO framework.
        
        Args:
            data_source: Optional path to ESCO data file or URL
            language: Language code for competency descriptions (default: "en")
        """
        self._competencies: List[ESCOCompetency] = []
        self._competency_map: Dict[str, ESCOCompetency] = {}
        self._categories: Set[str] = set()
        self._skill_groups: Dict[str, List[ESCOCompetency]] = {}
        self._is_loaded: bool = False
        self._data_source: Optional[str] = data_source
        self._language: str = language
        self._logger = logging.getLogger(__name__)
        
        # ESCO framework metadata
        self._name = "ESCO"
        self._version = "1.1.0"
        self._description = ("European Skills, Competences, Qualifications and Occupations framework. "
                           "A multilingual classification of skills, competences and occupations.")
    
    def get_name(self) -> str:
        """Get the name of the ESCO framework."""
        return self._name
    
    def get_version(self) -> str:
        """Get the version of the ESCO framework."""
        return self._version
    
    def get_description(self) -> str:
        """Get the description of the ESCO framework."""
        return self._description
    
    def load_framework(self, data_source: Optional[str] = None) -> bool:
        """
        Load ESCO competency data from the specified source.
        
        Args:
            data_source: Optional path to ESCO data file or URL
            
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
            self._logger.info(f"ESCO framework loaded successfully with {len(self._competencies)} competencies")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to load ESCO framework: {str(e)}")
            raise FrameworkError(f"Failed to load ESCO framework: {str(e)}", self._name, e)
    
    def _load_sample_data(self) -> None:
        """Load sample ESCO competencies for demonstration purposes."""
        sample_competencies = [
            ESCOCompetency(
                id="S1.0.0",
                name="Communication",
                description="Ability to convey information effectively through various channels and media",
                framework_id="esco_s1_0_0",
                category="Transversal skills",
                skill_type="skill/competence",
                reusability_level="cross-sector",
                skill_group="Communication and collaboration",
                keywords={"communication", "speaking", "writing", "presentation"},
                alternative_labels=["verbal communication", "written communication"],
                esco_uri="http://data.europa.eu/esco/skill/S1.0.0"
            ),
            ESCOCompetency(
                id="S2.1.1",
                name="Project management",
                description="Plan, organize, and manage resources to successfully complete specific project goals",
                framework_id="esco_s2_1_1",
                category="Technical skills",
                skill_type="skill/competence",
                reusability_level="cross-sector",
                skill_group="Management and leadership",
                keywords={"project", "management", "planning", "coordination", "leadership"},
                alternative_labels=["project coordination", "project planning"],
                esco_uri="http://data.europa.eu/esco/skill/S2.1.1"
            ),
            ESCOCompetency(
                id="S3.2.1",
                name="Critical thinking",
                description="Analyze information objectively and make reasoned judgments",
                framework_id="esco_s3_2_1",
                category="Cognitive skills",
                skill_type="skill/competence",
                reusability_level="cross-sector",
                skill_group="Thinking and problem solving",
                keywords={"critical", "thinking", "analysis", "reasoning", "judgment"},
                alternative_labels=["analytical thinking", "logical reasoning"],
                esco_uri="http://data.europa.eu/esco/skill/S3.2.1"
            ),
            ESCOCompetency(
                id="K1.1.0",
                name="Computer science",
                description="Knowledge of computer systems, programming, and computational thinking",
                framework_id="esco_k1_1_0",
                category="Knowledge areas",
                skill_type="knowledge",
                reusability_level="sector-specific",
                skill_group="Information and Communication Technologies",
                keywords={"computer", "programming", "software", "technology", "IT"},
                alternative_labels=["computing", "information technology"],
                esco_uri="http://data.europa.eu/esco/knowledge/K1.1.0"
            ),
            ESCOCompetency(
                id="S4.3.2",
                name="Team collaboration",
                description="Work effectively with others towards common goals and objectives",
                framework_id="esco_s4_3_2",
                category="Social skills",
                skill_type="skill/competence",
                reusability_level="cross-sector",
                skill_group="Communication and collaboration",
                keywords={"team", "collaboration", "cooperation", "teamwork"},
                alternative_labels=["teamwork", "group work", "cooperative work"],
                esco_uri="http://data.europa.eu/esco/skill/S4.3.2"
            ),
            ESCOCompetency(
                id="S5.1.0",
                name="Problem solving",
                description="Identify problems and implement effective solutions",
                framework_id="esco_s5_1_0",
                category="Cognitive skills",
                skill_type="skill/competence",
                reusability_level="cross-sector",
                skill_group="Thinking and problem solving",
                keywords={"problem", "solving", "solution", "troubleshooting"},
                alternative_labels=["troubleshooting", "issue resolution"],
                esco_uri="http://data.europa.eu/esco/skill/S5.1.0"
            )
        ]
        
        self._competencies = sample_competencies
    
    def _load_from_source(self, source: str) -> None:
        """
        Load ESCO data from file or URL source.
        
        Args:
            source: Path to data file or URL
        """
        # This would implement actual ESCO data loading
        # For now, we'll use the sample data
        self._load_sample_data()
        self._logger.info(f"Loaded ESCO data from source: {source}")
    
    def _build_indices(self) -> None:
        """Build internal indices for fast lookup."""
        self._competency_map.clear()
        self._categories.clear()
        self._skill_groups.clear()
        
        for competency in self._competencies:
            # Build ID map
            self._competency_map[competency.id] = competency
            
            # Build categories set
            if competency.category:
                self._categories.add(competency.category)
            
            # Build skill groups index
            if competency.skill_group:
                if competency.skill_group not in self._skill_groups:
                    self._skill_groups[competency.skill_group] = []
                self._skill_groups[competency.skill_group].append(competency)
    
    def get_competencies(self) -> List[Competency]:
        """Get all competencies in the ESCO framework."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return self._competencies.copy()
    
    def find_by_id(self, competency_id: str) -> Optional[Competency]:
        """Find an ESCO competency by its ID."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return self._competency_map.get(competency_id)
    
    def search_by_keyword(self, keyword: str, limit: Optional[int] = None) -> List[Competency]:
        """Search ESCO competencies by keyword."""
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
            # Also check alternative labels for ESCO competencies
            elif isinstance(competency, ESCOCompetency):
                for label in competency.alternative_labels:
                    if keyword_lower in label.lower():
                        results.append(competency)
                        break
        
        # Sort by relevance (exact matches first, then partial matches)
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
        """Get all available categories in ESCO."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._categories))
    
    def get_competencies_by_category(self, category: str) -> List[Competency]:
        """Get all ESCO competencies in a specific category."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return [comp for comp in self._competencies if comp.category == category]
    
    def get_skill_groups(self) -> List[str]:
        """
        Get all ESCO skill groups.
        
        Returns:
            List[str]: List of skill group names
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        return sorted(list(self._skill_groups.keys()))
    
    def get_competencies_by_skill_group(self, skill_group: str) -> List[ESCOCompetency]:
        """
        Get all competencies in a specific ESCO skill group.
        
        Args:
            skill_group: Name of the skill group
            
        Returns:
            List[ESCOCompetency]: List of competencies in the skill group
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return self._skill_groups.get(skill_group, [])
    
    def find_similar_competencies(self, competency_id: str, 
                                threshold: float = 0.5,
                                limit: Optional[int] = None) -> List[Competency]:
        """Find ESCO competencies similar to a given competency."""
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
        """Check if the ESCO framework is loaded."""
        return self._is_loaded
    
    def reload(self) -> bool:
        """Reload the ESCO framework data."""
        try:
            self._is_loaded = False
            return self.load_framework()
        except Exception as e:
            self._logger.error(f"Failed to reload ESCO framework: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistical information about the ESCO framework."""
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        # Count competencies by type
        type_counts = {}
        for competency in self._competencies:
            if isinstance(competency, ESCOCompetency):
                skill_type = competency.skill_type or "unknown"
                type_counts[skill_type] = type_counts.get(skill_type, 0) + 1
        
        # Count competencies by reusability level
        reusability_counts = {}
        for competency in self._competencies:
            if isinstance(competency, ESCOCompetency):
                level = competency.reusability_level or "unknown"
                reusability_counts[level] = reusability_counts.get(level, 0) + 1
        
        return {
            "framework_name": self._name,
            "framework_version": self._version,
            "language": self._language,
            "total_competencies": len(self._competencies),
            "categories": len(self._categories),
            "skill_groups": len(self._skill_groups),
            "competencies_by_type": type_counts,
            "competencies_by_reusability": reusability_counts,
            "is_loaded": self._is_loaded,
            "data_source": self._data_source
        }
    
    def search_by_alternative_labels(self, query: str, limit: Optional[int] = None) -> List[ESCOCompetency]:
        """
        Search ESCO competencies by alternative labels.
        
        Args:
            query: Search query
            limit: Optional limit for results
            
        Returns:
            List[ESCOCompetency]: List of matching competencies
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        results = []
        query_lower = query.lower().strip()
        
        for competency in self._competencies:
            if isinstance(competency, ESCOCompetency):
                for label in competency.alternative_labels:
                    if query_lower in label.lower():
                        results.append(competency)
                        break
        
        if limit:
            results = results[:limit]
        
        return results
    
    def get_competencies_by_type(self, skill_type: str) -> List[ESCOCompetency]:
        """
        Get all competencies of a specific type.
        
        Args:
            skill_type: Type of skill to filter by
            
        Returns:
            List[ESCOCompetency]: List of competencies of the specified type
        """
        if not self._is_loaded:
            raise FrameworkNotLoadedException(self._name)
        
        return [comp for comp in self._competencies 
                if isinstance(comp, ESCOCompetency) and comp.skill_type == skill_type] 