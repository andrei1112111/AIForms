from .branches_repository import BranchesRepository
from .commits_repository import CommitsRepository
from .developers_repository import DevelopersRepository
from .hotspots_repository import HotspotsRepository
from .projects_repository import ProjectsRepository
from .repositories_repository import RepositoriesRepository
from .kpi_commit_repository import KPICommitRepository

from src.db.session import Session


branchesRepository = BranchesRepository(Session())
commitsRepository = CommitsRepository(Session())
developersRepository = DevelopersRepository(Session())
hotspotsRepository = HotspotsRepository(Session())
projectsRepository = ProjectsRepository(Session())
repositoriesRepository = RepositoriesRepository(Session())
kpiCommitRepository = KPICommitRepository(Session())
__all__ = [
    "branchesRepository",
    "commitsRepository",
    "developersRepository",
    "hotspotsRepository",
    "projectsRepository",
    "repositoriesRepository",
	"kpiCommitRepository"
]
