#!/usr/bin/env python3
"""
Database seeder — idempotent, safe to call on every startup.

Seeds:
  • 100 Books
  • 500 Members
  • 200 Borrow records (mix of BORROWED and RETURNED)

If any books are already present, the seeder exits immediately without
writing anything — making it safe to run on every container start.

Per-member borrow limit: currently NONE is enforced by the application.
Each member can hold as many books simultaneously as have available copies.
Add a MAX_ACTIVE_BORROWS_PER_MEMBER constant here (and in BorrowService)
if you'd like to enforce one.
"""
import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from tortoise import Tortoise

from app.database import TORTOISE_ORM
from app.models.book import Book
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.member import Member

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")


# ── Seed data ─────────────────────────────────────────────────────────────────

GENRES = ["Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery",
          "Biography", "History", "Self-Help", "Romance", "Thriller"]

BOOK_TITLES = [
    "The Shadow of the Wind", "Dune", "Foundation", "Neuromancer",
    "The Name of the Wind", "A Little Life", "The Road", "Blood Meridian",
    "Beloved", "Pachinko", "The Kite Runner", "Shantaram", "Recursion",
    "Dark Matter", "The Martian", "Project Hail Mary", "Klara and the Sun",
    "Never Let Me Go", "The Remains of the Day", "Kazuo Ishiguro Collected",
    "Sapiens", "Homo Deus", "21 Lessons", "Thinking Fast and Slow",
    "The Power of Habit", "Atomic Habits", "Deep Work", "So Good They Can't",
    "The Pragmatic Programmer", "Clean Code", "Refactoring", "Design Patterns",
    "The Mythical Man-Month", "Code Complete", "Structure and Interpretation",
    "Gödel Escher Bach", "The Art of Problem Solving", "How to Solve It",
    "The Emperor's New Mind", "A Brief History of Time", "The Fabric of Reality",
    "Surely You're Joking Mr Feynman", "What Do You Care", "Feynman Lectures Vol 1",
    "The Selfish Gene", "The Extended Phenotype", "Guns Germs and Steel",
    "The Third Chimpanzee", "Collapse", "The World Until Yesterday",
    "Crime and Punishment", "The Brothers Karamazov", "The Idiot", "Notes from Underground",
    "War and Peace", "Anna Karenina", "The Death of Ivan Ilyich", "Hadji Murat",
    "One Hundred Years of Solitude", "Love in the Time of Cholera",
    "The General in His Labyrinth", "The Autumn of the Patriarch",
    "Midnight's Children", "The Satanic Verses", "The Ground Beneath Her Feet",
    "Shame", "East of Eden", "Of Mice and Men", "Cannery Row",
    "The Grapes of Wrath", "In Dubious Battle", "Travels with Charley",
    "Brave New World", "Nineteen Eighty-Four", "Animal Farm", "Island",
    "Point Counter Point", "Crome Yellow", "Those Barren Leaves",
    "The Trial", "The Castle", "Amerika", "In the Penal Colony",
    "Ulysses", "Dubliners", "A Portrait of the Artist", "Finnegans Wake",
    "To the Lighthouse", "Mrs Dalloway", "The Waves", "Orlando",
    "The Collector", "The Magus", "Daniel Martin", "A Maggot",
    "The French Lieutenant's Woman", "Atonement", "Saturday", "Solar",
    "Amsterdam", "The Comfort of Strangers", "Black Dogs", "The Innocent",
    "On Chesil Beach", "Enduring Love", "The Cement Garden",
]

AUTHORS = [
    "Carlos Ruiz Zafón", "Frank Herbert", "Isaac Asimov", "William Gibson",
    "Patrick Rothfuss", "Hanya Yanagihara", "Cormac McCarthy", "Toni Morrison",
    "Min Jin Lee", "Khaled Hosseini", "Gregory David Roberts",
    "Blake Crouch", "Andy Weir", "Kazuo Ishiguro", "Yuval Noah Harari",
    "Daniel Kahneman", "James Clear", "Cal Newport", "David Thomas",
    "Robert C. Martin", "Martin Fowler", "Gang of Four", "Frederick Brooks",
    "Douglas Hofstadter", "George Pólya", "Roger Penrose", "Richard Feynman",
    "Richard Dawkins", "Jared Diamond", "Fyodor Dostoevsky", "Leo Tolstoy",
    "Gabriel García Márquez", "Salman Rushdie", "John Steinbeck",
    "Aldous Huxley", "George Orwell", "Franz Kafka", "James Joyce",
    "Virginia Woolf", "John Fowles", "Ian McEwan",
]

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry",
    "Iris", "James", "Karen", "Leo", "Mia", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zoe", "Aiden", "Bella", "Carlos", "Diana", "Ethan", "Fiona",
    "George", "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Mike", "Nina",
    "Oscar", "Paula", "Ryan", "Sofia", "Tom", "Uma", "Vera", "Will",
    "Xena", "Yasmin",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White",
    "Harris", "Martin", "Thompson", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams",
    "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter",
    "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Sanchez",
    "Rogers",
]


# ── Seeder ────────────────────────────────────────────────────────────────────

def _random_isbn() -> str:
    return "978" + "".join(str(random.randint(0, 9)) for _ in range(10))


async def seed_books(n: int = 100) -> list[Book]:
    logger.info("Seeding %d books…", n)
    books = []
    used_isbns: set[str] = set()
    titles = list(BOOK_TITLES)
    random.shuffle(titles)

    for i in range(n):
        isbn = _random_isbn()
        while isbn in used_isbns:
            isbn = _random_isbn()
        used_isbns.add(isbn)

        total = random.randint(2, 8)
        book = await Book.create(
            title=titles[i % len(titles)] + (f" Vol. {i // len(titles) + 1}" if i >= len(titles) else ""),
            author=random.choice(AUTHORS),
            isbn=isbn,
            genre=random.choice(GENRES),
            total_copies=total,
            available_copies=total,
            published_year=random.randint(1950, 2024),
        )
        books.append(book)

    logger.info(" %d books created", n)
    return books


async def seed_members(n: int = 500) -> list[Member]:
    logger.info("Seeding %d members…", n)
    members = []
    used_emails: set[str] = set()

    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        base = f"{first.lower()}.{last.lower()}"
        email = f"{base}@library.example"

        # guarantee uniqueness
        suffix = 1
        candidate = email
        while candidate in used_emails:
            candidate = f"{base}{suffix}@library.example"
            suffix += 1
        used_emails.add(candidate)

        member = await Member.create(
            name=f"{first} {last}",
            email=candidate,
            is_active=random.random() > 0.05,  # ~5% inactive
        )
        members.append(member)

    logger.info("  ✓ %d members created", n)
    return members


async def seed_borrows(books: list[Book], members: list[Member], n: int = 200) -> None:
    logger.info("Seeding %d borrow records…", n)
    now = datetime.now(timezone.utc)

    # track active borrows per (book, member) to avoid duplicates
    active_borrows: set[tuple[int, int]] = set()
    # track available copies so we don't over-borrow
    available: dict[int, int] = {b.id: b.available_copies for b in books}

    active_members = [m for m in members if m.is_active]
    created = 0
    attempts = 0

    while created < n and attempts < n * 10:
        attempts += 1
        book = random.choice(books)
        member = random.choice(active_members)

        if available[book.id] <= 0:
            continue
        if (book.id, member.id) in active_borrows:
            continue

        # Decide if this ends up returned or still borrowed
        will_return = random.random() < 0.6  # 60% returned

        # Random borrow date in the last 90 days
        days_ago = random.randint(1, 90)
        borrowed_at = now - timedelta(days=days_ago)
        due_date = borrowed_at + timedelta(days=14)

        if will_return:
            days_held = random.randint(1, min(days_ago, 21))
            returned_at = borrowed_at + timedelta(days=days_held)
            status = BorrowStatus.RETURNED
        else:
            returned_at = None
            status = BorrowStatus.OVERDUE if due_date < now else BorrowStatus.BORROWED
            active_borrows.add((book.id, member.id))
            available[book.id] -= 1

        await BorrowRecord.create(
            book_id=book.id,
            member_id=member.id,
            borrowed_at=borrowed_at,
            due_date=due_date,
            returned_at=returned_at,
            status=status,
        )
        created += 1

    # Persist adjusted available_copies back to the Book rows
    for book in books:
        if book.available_copies != available[book.id]:
            await Book.filter(id=book.id).update(available_copies=available[book.id])

    logger.info("%d borrow records created (%d RETURNED, %d active)",
                created,
                created - len(active_borrows),
                len(active_borrows))


async def main() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)

    try:
        count = await Book.all().count()
        if count > 0:
            logger.info(
                "Seed skipped - database already contains %d book(s). "
                "Drop the postgres_data volume to reseed.",
                count,
            )
            return

        logger.info("Starting seed…")
        books = await seed_books(100)
        members = await seed_members(500)
        await seed_borrows(books, members, 200)
        logger.info("Seed complete ✓")
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
