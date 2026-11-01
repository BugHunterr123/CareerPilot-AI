"""v2: token version on users, runnable coding questions, timed practice tests

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as b:
        b.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
        b.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("practice_questions") as b:
        b.add_column(sa.Column("qkey", sa.String(length=80), nullable=True))
        b.add_column(sa.Column("title", sa.String(length=160), nullable=False, server_default=""))
        b.add_column(sa.Column("tests", sa.JSON(), nullable=True))
        b.add_column(sa.Column("starter_code", sa.Text(), nullable=False, server_default=""))
        b.add_column(sa.Column("io_format", sa.JSON(), nullable=True))
        b.add_column(sa.Column("solutions_other", sa.JSON(), nullable=True))
        b.create_index("ix_practice_questions_qkey", ["qkey"], unique=True)

    op.create_table(
        "practice_tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("difficulty", sa.String(length=10), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_practice_tests_user_id", "practice_tests", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_practice_tests_user_id", table_name="practice_tests")
    op.drop_table("practice_tests")
    with op.batch_alter_table("practice_questions") as b:
        b.drop_index("ix_practice_questions_qkey")
        for c in ("solutions_other", "io_format", "starter_code", "tests", "title", "qkey"):
            b.drop_column(c)
    with op.batch_alter_table("users") as b:
        b.drop_column("last_login_at")
        b.drop_column("token_version")
