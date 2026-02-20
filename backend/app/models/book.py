from tortoise import fields
from tortoise.models import Model


class Book(Model):
    """Library book with copy tracking."""

    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255, db_index=True)
    author = fields.CharField(max_length=255, db_index=True)
    isbn = fields.CharField(max_length=13, unique=True, null=True)
    genre = fields.CharField(max_length=100, null=True)
    publisher = fields.CharField(max_length=255, null=True)
    total_copies = fields.IntField(default=1)
    available_copies = fields.IntField(default=1)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Reverse relation
    borrow_records: fields.ReverseRelation["BorrowRecord"]

    class Meta:
        table = "books"
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"
