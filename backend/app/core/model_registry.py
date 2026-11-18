
"""Register all SQLAlchemy models with the shared declarative Base."""

from app.users.models import User
from app.roles.models import Role

from app.institutions.models import Institution
from app.departments.models import Department
from app.profiles.models import AcademicProfile
from app.degrees.models import Degree
from app.publications.models import Publication
from app.research_projects.models import ResearchProject
from app.teaching_experience.models import TeachingExperience
from app.documents.models import Document

from app.academic_positions.models import AcademicPosition
from app.academic_ranks.models import AcademicRank
from app.employment_types.models import EmploymentType
from app.position_statuses.models import PositionStatus
from app.document_types.models import DocumentType
from app.position_required_documents.models import PositionRequiredDocument

from app.applications.models import Application
from app.application_documents.models import ApplicationDocument
from app.application_status_history.models import ApplicationStatusHistory

from app.evaluation_committees.models import EvaluationCommittee
from app.committee_members.models import CommitteeMember
from app.committee_applications.models import CommitteeApplication
from app.evaluation_criteria.models import EvaluationCriterion
from app.evaluation_scores.models import EvaluationScore
from app.evaluation_reports.models import EvaluationReport
from app.evaluation_results.models import EvaluationResult

from app.notifications.models import Notification

from app.ai.models import AIRun, AIArtifact, AIEvidence, AIReviewEvent
