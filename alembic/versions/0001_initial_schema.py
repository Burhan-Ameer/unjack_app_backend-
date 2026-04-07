"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-07 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'friendshipstatus') THEN
                CREATE TYPE friendshipstatus AS ENUM ('pending', 'accepted');
            END IF;
        END
        $$;
        """
    )

    friendship_status = postgresql.ENUM("pending", "accepted", name="friendshipstatus", create_type=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "app_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("app_name", sa.String(), nullable=True),
        sa.Column("package", sa.String(), nullable=True),
        sa.Column("duration", sa.BigInteger(), nullable=True),
        sa.Column("blocked_date", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_app_sessions_id", "app_sessions", ["id"], unique=False)

    op.create_table(
        "friendships",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("addressee_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", friendship_status, nullable=True),
    )
    op.create_index("ix_friendships_id", "friendships", ["id"], unique=False)

    op.create_table(
        "streaks",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("current_streak", sa.Integer(), nullable=True),
        sa.Column("longest_streak", sa.Integer(), nullable=True),
        sa.Column("total_focus_time", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_streaks_id", "streaks", ["id"], unique=False)
    op.create_index("ix_streaks_user_id", "streaks", ["user_id"], unique=True)

    op.create_table(
        "weekly_stats",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("week_start", sa.Date(), nullable=True),
        sa.Column("total_time", sa.BigInteger(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
    )
    op.create_index("ix_weekly_stats_id", "weekly_stats", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_weekly_stats_id", table_name="weekly_stats")
    op.drop_table("weekly_stats")

    op.drop_index("ix_streaks_user_id", table_name="streaks")
    op.drop_index("ix_streaks_id", table_name="streaks")
    op.drop_table("streaks")

    op.drop_index("ix_friendships_id", table_name="friendships")
    op.drop_table("friendships")

    op.drop_index("ix_app_sessions_id", table_name="app_sessions")
    op.drop_table("app_sessions")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS friendshipstatus")
