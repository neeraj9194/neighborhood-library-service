"""FastAPI dependency factories — inject services into route handlers via Depends()."""
from app.repositories.book import BookRepository
from app.repositories.borrow_record import BorrowRecordRepository
from app.repositories.member import MemberRepository
from app.services.book import BookService
from app.services.borrow import BorrowService
from app.services.member import MemberService
from app.services.stats import StatsService


def get_book_service() -> BookService:
    return BookService(repo=BookRepository())


def get_member_service() -> MemberService:
    return MemberService(repo=MemberRepository())


def get_borrow_service() -> BorrowService:
    return BorrowService(
        borrow_repo=BorrowRecordRepository(),
        book_repo=BookRepository(),
        member_repo=MemberRepository(),
    )


def get_stats_service() -> StatsService:
    return StatsService()
