"""
Concrete repository implementations using SQLAlchemy for the competency assessment system.

This module provides concrete implementations of the repository interfaces
defined in the repositories package. These implementations use SQLAlchemy
ORM for data persistence and provide full CRUD operations with proper
error handling and transaction management.

Classes:
    BaseSQLRepository: Abstract base class for SQL repositories
    SQLUserRepository: User repository implementation
    SQLAssessmentRepository: Assessment repository implementation
    SQLSkillRepository: Skill repository implementation
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import and_, or_, func, desc

from ..repositories.interfaces import (
    UserRepository, AssessmentRepository, SkillRepository,
    RepositoryError, NotFoundException, ValidationError
)
from ..domain.models import User, Assessment, Skill, Profile, Evidence, Conversation, Message, MappedCompetency
from ..enums import UserRole, AssessmentStatus, ProficiencyLevel
from .models import (
    UserModel, AssessmentModel, SkillModel, ProfileModel, EvidenceModel,
    ConversationModel, MessageModel, MappedCompetencyModel
)
from .connection import DatabaseManager


class BaseSQLRepository:
    """
    Abstract base class for SQL-based repositories.
    
    This base class provides common functionality for all SQL repositories,
    including database session management, error handling, and utility methods
    for converting between domain models and database models.
    
    Attributes:
        db_manager: Database manager for connection handling
        logger: Logger for repository operations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize base repository.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _handle_db_error(self, error: Exception, operation: str) -> None:
        """
        Handle database errors and convert to appropriate repository exceptions.
        
        Args:
            error: Database exception
            operation: Description of the operation that failed
        """
        self.logger.error(f"Database error during {operation}: {str(error)}")
        
        if isinstance(error, IntegrityError):
            raise ValidationError("Repository", [f"Data integrity violation: {str(error)}"])
        elif isinstance(error, SQLAlchemyError):
            raise RepositoryError(f"Database error during {operation}: {str(error)}", error)
        else:
            raise RepositoryError(f"Unexpected error during {operation}: {str(error)}", error)


class SQLUserRepository(BaseSQLRepository, UserRepository):
    """
    SQLAlchemy implementation of UserRepository.
    
    This repository provides full CRUD operations for users, including
    profile management and assessment relationships. It handles the mapping
    between User domain objects and UserModel database entities.
    """
    
    def save(self, user: User) -> bool:
        """Save a user to the database."""
        try:
            with self.db_manager.session_scope() as session:
                # Check if user already exists
                existing = session.query(UserModel).filter_by(id=user.id).first()
                
                if existing:
                    # Update existing user
                    existing.email = user.email
                    existing.password_hash = user.password_hash
                    existing.role = user.role
                    existing.last_login = user.last_login
                    
                    # Update profile if it exists
                    if user.profile:
                        if existing.profile:
                            self._update_profile_model(existing.profile, user.profile)
                        else:
                            profile_model = self._create_profile_model(user.profile, user.id)
                            session.add(profile_model)
                else:
                    # Create new user
                    user_model = UserModel(
                        id=user.id,
                        email=user.email,
                        password_hash=user.password_hash,
                        role=user.role,
                        last_login=user.last_login
                    )
                    session.add(user_model)
                    
                    # Add profile if it exists
                    if user.profile:
                        profile_model = self._create_profile_model(user.profile, user.id)
                        session.add(profile_model)
                
                session.commit()
                self.logger.info(f"User saved successfully: {user.id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "user save")
            return False
    
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by ID."""
        try:
            with self.db_manager.session_scope() as session:
                user_model = session.query(UserModel).options(
                    joinedload(UserModel.profile).joinedload(ProfileModel.skills).joinedload(SkillModel.evidences),
                    joinedload(UserModel.assessments)
                ).filter_by(id=user_id).first()
                
                if not user_model:
                    return None
                
                return self._convert_to_domain_user(user_model)
                
        except Exception as e:
            self._handle_db_error(e, "user find by ID")
            return None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        try:
            with self.db_manager.session_scope() as session:
                user_model = session.query(UserModel).options(
                    joinedload(UserModel.profile),
                    joinedload(UserModel.assessments)
                ).filter_by(email=email).first()
                
                if not user_model:
                    return None
                
                return self._convert_to_domain_user(user_model)
                
        except Exception as e:
            self._handle_db_error(e, "user find by email")
            return None
    
    def find_by_role(self, role: UserRole) -> List[User]:
        """Find all users with a specific role."""
        try:
            with self.db_manager.session_scope() as session:
                user_models = session.query(UserModel).filter_by(role=role).all()
                return [self._convert_to_domain_user(model) for model in user_models]
                
        except Exception as e:
            self._handle_db_error(e, "user find by role")
            return []
    
    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[User]:
        """Retrieve all users with pagination."""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(UserModel).offset(offset)
                if limit:
                    query = query.limit(limit)
                
                user_models = query.all()
                return [self._convert_to_domain_user(model) for model in user_models]
                
        except Exception as e:
            self._handle_db_error(e, "user find all")
            return []
    
    def update(self, user: User) -> bool:
        """Update an existing user."""
        try:
            with self.db_manager.session_scope() as session:
                user_model = session.query(UserModel).filter_by(id=user.id).first()
                if not user_model:
                    raise NotFoundException("User", user.id)
                
                # Update user fields
                user_model.email = user.email
                user_model.password_hash = user.password_hash
                user_model.role = user.role
                user_model.last_login = user.last_login
                
                session.commit()
                self.logger.info(f"User updated successfully: {user.id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "user update")
            return False
    
    def delete(self, user_id: str) -> bool:
        """Delete a user from the database."""
        try:
            with self.db_manager.session_scope() as session:
                user_model = session.query(UserModel).filter_by(id=user_id).first()
                if not user_model:
                    raise NotFoundException("User", user_id)
                
                session.delete(user_model)
                session.commit()
                self.logger.info(f"User deleted successfully: {user_id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "user delete")
            return False
    
    def exists(self, user_id: str) -> bool:
        """Check if a user exists."""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(UserModel).filter_by(id=user_id).first() is not None
                
        except Exception as e:
            self._handle_db_error(e, "user exists check")
            return False
    
    def count(self) -> int:
        """Get total user count."""
        try:
            with self.db_manager.session_scope() as session:
                return session.query(UserModel).count()
                
        except Exception as e:
            self._handle_db_error(e, "user count")
            return 0
    
    def find_by_last_login_before(self, date: datetime) -> List[User]:
        """Find users who haven't logged in since a specific date."""
        try:
            with self.db_manager.session_scope() as session:
                user_models = session.query(UserModel).filter(
                    or_(
                        UserModel.last_login.is_(None),
                        UserModel.last_login < date
                    )
                ).all()
                
                return [self._convert_to_domain_user(model) for model in user_models]
                
        except Exception as e:
            self._handle_db_error(e, "user find by last login")
            return []
    
    def _convert_to_domain_user(self, user_model: UserModel) -> User:
        """Convert UserModel to User domain object."""
        user = User(
            id=str(user_model.id),
            email=user_model.email,
            password_hash=user_model.password_hash,
            role=user_model.role,
            last_login=user_model.last_login,
            created_at=user_model.created_at
        )
        
        # Convert profile if it exists
        if user_model.profile:
            user.profile = self._convert_to_domain_profile(user_model.profile)
        
        # Convert assessments (basic conversion without full details)
        for assessment_model in user_model.assessments:
            assessment = Assessment(
                id=str(assessment_model.id),
                user_id=str(assessment_model.user_id),
                status=assessment_model.status,
                started_at=assessment_model.started_at,
                completed_at=assessment_model.completed_at
            )
            user.assessments.append(assessment)
        
        return user
    
    def _convert_to_domain_profile(self, profile_model: ProfileModel) -> Profile:
        """Convert ProfileModel to Profile domain object."""
        profile = Profile(
            user_id=str(profile_model.user_id),
            first_name=profile_model.first_name,
            last_name=profile_model.last_name,
            preferred_language=profile_model.preferred_language,
            volunteering_background=profile_model.volunteering_background
        )
        
        # Convert skills
        for skill_model in profile_model.skills:
            skill = Skill(
                id=str(skill_model.id),
                name=skill_model.name,
                description=skill_model.description,
                level=skill_model.level,
                framework_source=skill_model.framework_source,
                framework_id=skill_model.framework_id,
                acquired_date=skill_model.acquired_date,
                user_id=str(profile_model.user_id)
            )
            profile.skills.append(skill)
        
        return profile
    
    def _create_profile_model(self, profile: Profile, user_id: str) -> ProfileModel:
        """Create ProfileModel from Profile domain object."""
        return ProfileModel(
            user_id=user_id,
            first_name=profile.first_name,
            last_name=profile.last_name,
            preferred_language=profile.preferred_language,
            volunteering_background=profile.volunteering_background
        )
    
    def _update_profile_model(self, profile_model: ProfileModel, profile: Profile) -> None:
        """Update ProfileModel with Profile domain object data."""
        profile_model.first_name = profile.first_name
        profile_model.last_name = profile.last_name
        profile_model.preferred_language = profile.preferred_language
        profile_model.volunteering_background = profile.volunteering_background


class SQLAssessmentRepository(BaseSQLRepository, AssessmentRepository):
    """
    SQLAlchemy implementation of AssessmentRepository.
    
    This repository handles assessment data persistence including conversation
    and mapped competency relationships.
    """
    
    def save(self, assessment: Assessment) -> bool:
        """Save an assessment to the database."""
        try:
            with self.db_manager.session_scope() as session:
                existing = session.query(AssessmentModel).filter_by(id=assessment.id).first()
                
                if existing:
                    # Update existing assessment
                    existing.status = assessment.status
                    existing.started_at = assessment.started_at
                    existing.completed_at = assessment.completed_at
                    existing.framework_name = assessment.framework.get_name() if assessment.framework else None
                else:
                    # Create new assessment
                    assessment_model = AssessmentModel(
                        id=assessment.id,
                        user_id=assessment.user_id,
                        status=assessment.status,
                        started_at=assessment.started_at,
                        completed_at=assessment.completed_at,
                        framework_name=assessment.framework.get_name() if assessment.framework else None
                    )
                    session.add(assessment_model)
                
                session.commit()
                self.logger.info(f"Assessment saved successfully: {assessment.id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "assessment save")
            return False
    
    def find_by_id(self, assessment_id: str) -> Optional[Assessment]:
        """Find an assessment by ID."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_model = session.query(AssessmentModel).options(
                    joinedload(AssessmentModel.conversation).joinedload(ConversationModel.messages),
                    joinedload(AssessmentModel.mapped_competencies)
                ).filter_by(id=assessment_id).first()
                
                if not assessment_model:
                    return None
                
                return self._convert_to_domain_assessment(assessment_model)
                
        except Exception as e:
            self._handle_db_error(e, "assessment find by ID")
            return None
    
    def find_by_user_id(self, user_id: str) -> List[Assessment]:
        """Find all assessments for a user."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_models = session.query(AssessmentModel).filter_by(user_id=user_id).all()
                return [self._convert_to_domain_assessment(model) for model in assessment_models]
                
        except Exception as e:
            self._handle_db_error(e, "assessment find by user ID")
            return []
    
    def find_by_status(self, status: AssessmentStatus) -> List[Assessment]:
        """Find all assessments with a specific status."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_models = session.query(AssessmentModel).filter_by(status=status).all()
                return [self._convert_to_domain_assessment(model) for model in assessment_models]
                
        except Exception as e:
            self._handle_db_error(e, "assessment find by status")
            return []
    
    def find_by_user_and_status(self, user_id: str, status: AssessmentStatus) -> List[Assessment]:
        """Find assessments for a user with specific status."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_models = session.query(AssessmentModel).filter_by(
                    user_id=user_id, status=status
                ).all()
                return [self._convert_to_domain_assessment(model) for model in assessment_models]
                
        except Exception as e:
            self._handle_db_error(e, "assessment find by user and status")
            return []
    
    def update_status(self, assessment_id: str, status: AssessmentStatus) -> bool:
        """Update assessment status."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_model = session.query(AssessmentModel).filter_by(id=assessment_id).first()
                if not assessment_model:
                    raise NotFoundException("Assessment", assessment_id)
                
                assessment_model.status = status
                session.commit()
                self.logger.info(f"Assessment status updated: {assessment_id} -> {status}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "assessment status update")
            return False
    
    def update(self, assessment: Assessment) -> bool:
        """Update an existing assessment."""
        return self.save(assessment)  # Same logic as save for updates
    
    def delete(self, assessment_id: str) -> bool:
        """Delete an assessment."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_model = session.query(AssessmentModel).filter_by(id=assessment_id).first()
                if not assessment_model:
                    raise NotFoundException("Assessment", assessment_id)
                
                session.delete(assessment_model)
                session.commit()
                self.logger.info(f"Assessment deleted: {assessment_id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "assessment delete")
            return False
    
    def find_completed_between_dates(self, start_date: datetime, end_date: datetime) -> List[Assessment]:
        """Find assessments completed within date range."""
        try:
            with self.db_manager.session_scope() as session:
                assessment_models = session.query(AssessmentModel).filter(
                    and_(
                        AssessmentModel.status == AssessmentStatus.COMPLETED,
                        AssessmentModel.completed_at >= start_date,
                        AssessmentModel.completed_at <= end_date
                    )
                ).all()
                return [self._convert_to_domain_assessment(model) for model in assessment_models]
                
        except Exception as e:
            self._handle_db_error(e, "assessment find by date range")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get assessment statistics."""
        try:
            with self.db_manager.session_scope() as session:
                total_count = session.query(AssessmentModel).count()
                
                # Count by status
                status_counts = {}
                for status in AssessmentStatus:
                    count = session.query(AssessmentModel).filter_by(status=status).count()
                    status_counts[status.value] = count
                
                # Average completion time for completed assessments
                completed_assessments = session.query(AssessmentModel).filter(
                    and_(
                        AssessmentModel.status == AssessmentStatus.COMPLETED,
                        AssessmentModel.started_at.isnot(None),
                        AssessmentModel.completed_at.isnot(None)
                    )
                ).all()
                
                avg_duration = None
                if completed_assessments:
                    durations = [
                        (a.completed_at - a.started_at).total_seconds()
                        for a in completed_assessments
                    ]
                    avg_duration = sum(durations) / len(durations)
                
                return {
                    "total_assessments": total_count,
                    "status_distribution": status_counts,
                    "completed_count": len(completed_assessments),
                    "average_duration_seconds": avg_duration
                }
                
        except Exception as e:
            self._handle_db_error(e, "assessment statistics")
            return {}
    
    def find_incomplete_older_than(self, days: int) -> List[Assessment]:
        """Find incomplete assessments older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self.db_manager.session_scope() as session:
                assessment_models = session.query(AssessmentModel).filter(
                    and_(
                        AssessmentModel.status.in_([
                            AssessmentStatus.NOT_STARTED,
                            AssessmentStatus.IN_PROGRESS,
                            AssessmentStatus.PAUSED
                        ]),
                        AssessmentModel.created_at < cutoff_date
                    )
                ).all()
                
                return [self._convert_to_domain_assessment(model) for model in assessment_models]
                
        except Exception as e:
            self._handle_db_error(e, "assessment find incomplete older than")
            return []
    
    def _convert_to_domain_assessment(self, assessment_model: AssessmentModel) -> Assessment:
        """Convert AssessmentModel to Assessment domain object."""
        assessment = Assessment(
            id=str(assessment_model.id),
            user_id=str(assessment_model.user_id),
            status=assessment_model.status,
            started_at=assessment_model.started_at,
            completed_at=assessment_model.completed_at
        )
        
        # Convert conversation if it exists
        if assessment_model.conversation:
            conversation = Conversation(
                id=str(assessment_model.conversation.id),
                assessment_id=str(assessment_model.id),
                state=assessment_model.conversation.state,
                current_phase=assessment_model.conversation.current_phase,
                metadata=assessment_model.conversation.metadata or {}
            )
            
            # Convert messages
            for message_model in assessment_model.conversation.messages:
                message = Message(
                    id=str(message_model.id),
                    type=message_model.type,
                    content=message_model.content,
                    sender=message_model.sender,
                    timestamp=message_model.created_at,
                    metadata=message_model.metadata or {},
                    conversation_id=str(conversation.id)
                )
                conversation.messages.append(message)
            
            assessment.conversation = conversation
        
        # Convert mapped competencies
        for comp_model in assessment_model.mapped_competencies:
            mapped_comp = MappedCompetency(
                id=str(comp_model.id),
                competency_id=comp_model.competency_id,
                competency_name=comp_model.competency_name,
                confidence_score=comp_model.confidence_score,
                supporting_evidence=comp_model.supporting_evidence or [],
                assessment_id=str(assessment.id),
                framework_source=comp_model.framework_source,
                metadata=comp_model.metadata or {}
            )
            assessment.mapped_competencies.append(mapped_comp)
        
        return assessment


class SQLSkillRepository(BaseSQLRepository, SkillRepository):
    """
    SQLAlchemy implementation of SkillRepository.
    
    This repository handles skill data persistence including evidence relationships.
    """
    
    def save(self, skill: Skill) -> bool:
        """Save a skill to the database."""
        try:
            with self.db_manager.session_scope() as session:
                existing = session.query(SkillModel).filter_by(id=skill.id).first()
                
                if existing:
                    # Update existing skill
                    existing.name = skill.name
                    existing.description = skill.description
                    existing.level = skill.level
                    existing.framework_source = skill.framework_source
                    existing.framework_id = skill.framework_id
                    existing.acquired_date = skill.acquired_date
                else:
                    # Find profile for this skill
                    profile = session.query(ProfileModel).filter_by(user_id=skill.user_id).first()
                    if not profile:
                        raise RepositoryError(f"Profile not found for user {skill.user_id}")
                    
                    # Create new skill
                    skill_model = SkillModel(
                        id=skill.id,
                        profile_id=profile.id,
                        name=skill.name,
                        description=skill.description,
                        level=skill.level,
                        framework_source=skill.framework_source,
                        framework_id=skill.framework_id,
                        acquired_date=skill.acquired_date
                    )
                    session.add(skill_model)
                
                session.commit()
                self.logger.info(f"Skill saved successfully: {skill.id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "skill save")
            return False
    
    def find_by_id(self, skill_id: str) -> Optional[Skill]:
        """Find a skill by ID."""
        try:
            with self.db_manager.session_scope() as session:
                skill_model = session.query(SkillModel).options(
                    joinedload(SkillModel.evidences),
                    joinedload(SkillModel.profile)
                ).filter_by(id=skill_id).first()
                
                if not skill_model:
                    return None
                
                return self._convert_to_domain_skill(skill_model)
                
        except Exception as e:
            self._handle_db_error(e, "skill find by ID")
            return None
    
    def find_by_user_id(self, user_id: str) -> List[Skill]:
        """Find all skills for a user."""
        try:
            with self.db_manager.session_scope() as session:
                skill_models = session.query(SkillModel).join(ProfileModel).filter(
                    ProfileModel.user_id == user_id
                ).all()
                
                return [self._convert_to_domain_skill(model) for model in skill_models]
                
        except Exception as e:
            self._handle_db_error(e, "skill find by user ID")
            return []
    
    def search_by_name(self, name: str, exact_match: bool = False) -> List[Skill]:
        """Search skills by name."""
        try:
            with self.db_manager.session_scope() as session:
                if exact_match:
                    skill_models = session.query(SkillModel).filter_by(name=name).all()
                else:
                    skill_models = session.query(SkillModel).filter(
                        SkillModel.name.ilike(f"%{name}%")
                    ).all()
                
                return [self._convert_to_domain_skill(model) for model in skill_models]
                
        except Exception as e:
            self._handle_db_error(e, "skill search by name")
            return []
    
    def find_by_framework(self, framework_source: str, framework_id: Optional[str] = None) -> List[Skill]:
        """Find skills linked to a framework."""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(SkillModel).filter_by(framework_source=framework_source)
                
                if framework_id:
                    query = query.filter_by(framework_id=framework_id)
                
                skill_models = query.all()
                return [self._convert_to_domain_skill(model) for model in skill_models]
                
        except Exception as e:
            self._handle_db_error(e, "skill find by framework")
            return []
    
    def update(self, skill: Skill) -> bool:
        """Update an existing skill."""
        return self.save(skill)  # Same logic as save for updates
    
    def delete(self, skill_id: str) -> bool:
        """Delete a skill."""
        try:
            with self.db_manager.session_scope() as session:
                skill_model = session.query(SkillModel).filter_by(id=skill_id).first()
                if not skill_model:
                    raise NotFoundException("Skill", skill_id)
                
                session.delete(skill_model)
                session.commit()
                self.logger.info(f"Skill deleted: {skill_id}")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "skill delete")
            return False
    
    def find_by_proficiency_level(self, level: ProficiencyLevel) -> List[Skill]:
        """Find skills by proficiency level."""
        try:
            with self.db_manager.session_scope() as session:
                skill_models = session.query(SkillModel).filter_by(level=level).all()
                return [self._convert_to_domain_skill(model) for model in skill_models]
                
        except Exception as e:
            self._handle_db_error(e, "skill find by proficiency level")
            return []
    
    def get_skill_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get skill statistics."""
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(SkillModel)
                
                if user_id:
                    query = query.join(ProfileModel).filter(ProfileModel.user_id == user_id)
                
                total_count = query.count()
                
                # Count by proficiency level
                level_counts = {}
                for level in ProficiencyLevel:
                    count = query.filter_by(level=level).count()
                    level_counts[level.value] = count
                
                # Count by framework
                framework_counts = {}
                frameworks = session.query(SkillModel.framework_source).distinct().all()
                for (framework,) in frameworks:
                    if framework:
                        count = query.filter_by(framework_source=framework).count()
                        framework_counts[framework] = count
                
                return {
                    "total_skills": total_count,
                    "level_distribution": level_counts,
                    "framework_distribution": framework_counts
                }
                
        except Exception as e:
            self._handle_db_error(e, "skill statistics")
            return {}
    
    def find_popular_skills(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Find most popular skills."""
        try:
            with self.db_manager.session_scope() as session:
                popular_skills = session.query(
                    SkillModel.name,
                    func.count(SkillModel.id).label('count')
                ).group_by(SkillModel.name).order_by(
                    desc('count')
                ).limit(limit).all()
                
                return [
                    {"skill_name": name, "user_count": count}
                    for name, count in popular_skills
                ]
                
        except Exception as e:
            self._handle_db_error(e, "skill find popular")
            return []
    
    def find_similar_skills(self, skill_id: str, similarity_threshold: float = 0.7) -> List[Skill]:
        """Find similar skills (basic implementation)."""
        try:
            with self.db_manager.session_scope() as session:
                reference_skill = session.query(SkillModel).filter_by(id=skill_id).first()
                if not reference_skill:
                    return []
                
                # Simple similarity based on name and framework
                similar_skills = session.query(SkillModel).filter(
                    and_(
                        SkillModel.id != skill_id,
                        or_(
                            SkillModel.name.ilike(f"%{reference_skill.name}%"),
                            SkillModel.framework_source == reference_skill.framework_source
                        )
                    )
                ).all()
                
                return [self._convert_to_domain_skill(model) for model in similar_skills]
                
        except Exception as e:
            self._handle_db_error(e, "skill find similar")
            return []
    
    def bulk_save(self, skills: List[Skill]) -> bool:
        """Save multiple skills in bulk."""
        try:
            with self.db_manager.session_scope() as session:
                for skill in skills:
                    existing = session.query(SkillModel).filter_by(id=skill.id).first()
                    
                    if existing:
                        # Update existing
                        existing.name = skill.name
                        existing.description = skill.description
                        existing.level = skill.level
                        existing.framework_source = skill.framework_source
                        existing.framework_id = skill.framework_id
                        existing.acquired_date = skill.acquired_date
                    else:
                        # Find profile
                        profile = session.query(ProfileModel).filter_by(user_id=skill.user_id).first()
                        if not profile:
                            continue  # Skip skills without valid profiles
                        
                        # Create new
                        skill_model = SkillModel(
                            id=skill.id,
                            profile_id=profile.id,
                            name=skill.name,
                            description=skill.description,
                            level=skill.level,
                            framework_source=skill.framework_source,
                            framework_id=skill.framework_id,
                            acquired_date=skill.acquired_date
                        )
                        session.add(skill_model)
                
                session.commit()
                self.logger.info(f"Bulk saved {len(skills)} skills")
                return True
                
        except Exception as e:
            self._handle_db_error(e, "skill bulk save")
            return False
    
    def _convert_to_domain_skill(self, skill_model: SkillModel) -> Skill:
        """Convert SkillModel to Skill domain object."""
        skill = Skill(
            id=str(skill_model.id),
            name=skill_model.name,
            description=skill_model.description,
            level=skill_model.level,
            framework_source=skill_model.framework_source,
            framework_id=skill_model.framework_id,
            acquired_date=skill_model.acquired_date,
            user_id=str(skill_model.profile.user_id) if skill_model.profile else ""
        )
        
        # Convert evidence
        for evidence_model in skill_model.evidences:
            evidence = Evidence(
                id=str(evidence_model.id),
                description=evidence_model.description,
                date=evidence_model.date,
                conversation_id=str(evidence_model.conversation_id) if evidence_model.conversation_id else None,
                type=evidence_model.type,
                extracted_text=evidence_model.extracted_text,
                skill_id=str(skill.id),
                metadata=evidence_model.metadata or {}
            )
            skill.evidences.append(evidence)
        
        return skill 