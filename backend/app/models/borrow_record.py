import enum

from tortoise import fields
from tortoise.models import Model


class BorrowStatus(str, enum.Enum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class BorrowRecord(Model):
    """Tracks book borrowing and return operations."""

    id = fields.IntField(primary_key=True)
    book = fields.ForeignKeyField("models.Book", related_name="borrow_records", on_delete=fields.CASCADE)
    member = fields.ForeignKeyField("models.Member", related_name="borrow_records", on_delete=fields.CASCADE)
    borrowed_at = fields.DatetimeField(auto_now_add=True)
    due_date = fields.DatetimeField()
    returned_at = fields.DatetimeField(null=True)
    status = fields.CharEnumField(BorrowStatus, default=BorrowStatus.BORROWED, max_length=20)

    class Meta:
        table = "borrow_records"
        ordering = ["-borrowed_at"]

    def __str__(self) -> str:
        return f"BorrowRecord({self.id}: {self.status})"
