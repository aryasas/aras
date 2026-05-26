"""add ticket module

Revision ID: 20260526_0003
Revises: 20260526_0002
Create Date: 2026-05-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260526_0003'
down_revision: Union[str, None] = '20260526_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Team
    op.create_table('erp_ticket_teams',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_assignee_id', sa.Integer(), nullable=True),
        sa.Column('is_shared', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['default_assignee_id'], ['auth_users.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['erp_config_organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_erp_ticket_teams_org_id'), 'erp_ticket_teams', ['org_id'], unique=False)
    op.create_index(op.f('ix_erp_ticket_teams_is_shared'), 'erp_ticket_teams', ['is_shared'], unique=False)

    # Category
    op.create_table('erp_ticket_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('sla_hours', sa.Float(), default=24, nullable=False),
        sa.Column('is_shared', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['erp_config_organizations.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['erp_ticket_teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_erp_ticket_categories_org_id'), 'erp_ticket_categories', ['org_id'], unique=False)
    op.create_index(op.f('ix_erp_ticket_categories_is_shared'), 'erp_ticket_categories', ['is_shared'], unique=False)

    # Ticket
    op.create_table('erp_ticket_tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ticket_type', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=10), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('requester_name', sa.String(length=200), nullable=True),
        sa.Column('requester_email', sa.String(length=100), nullable=True),
        sa.Column('party_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['auth_users.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['erp_ticket_categories.id'], ),
        sa.ForeignKeyConstraint(['org_id'], ['erp_config_organizations.id'], ),
        sa.ForeignKeyConstraint(['party_id'], ['erp_party_parties.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['erp_ticket_teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_erp_ticket_tickets_org_id'), 'erp_ticket_tickets', ['org_id'], unique=False)

    # Message
    op.create_table('erp_ticket_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), default=False, nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['auth_users.id'], ),
        sa.ForeignKeyConstraint(['ticket_id'], ['erp_ticket_tickets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('erp_ticket_messages')
    op.drop_table('erp_ticket_tickets')
    op.drop_table('erp_ticket_categories')
    op.drop_table('erp_ticket_teams')
