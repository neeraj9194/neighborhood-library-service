from tortoise import fields
from tortoise.models import Model


class Member(Model):
    """Library member with soft-delete support."""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, db_index=True)
    email = fields.CharField(max_length=255, unique=True)
    phone = fields.CharField(max_length=20, null=True)
    address = fields.CharField(max_length=500, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Reverse relation
    borrow_records: fields.ReverseRelation["BorrowRecord"]

    class Meta:
        table = "members"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"
