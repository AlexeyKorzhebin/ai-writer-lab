"""initial schema

Revision ID: 7e33e9dfac5f
Revises: 
Create Date: 2026-03-15 11:44:36.867255

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e33e9dfac5f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(255), nullable=True),
        sa.Column('temperature', sa.String(50), nullable=True),
        sa.Column('max_tokens', sa.String(50), nullable=True),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('author_style', sa.Text(), nullable=True),
    )
    op.create_index('ix_projects_id', 'projects', ['id'])

    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
    )
    op.create_index('ix_chapters_id', 'chapters', ['id'])

    op.create_table(
        'chapter_versions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('chapter_id', sa.Integer(), sa.ForeignKey('chapters.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
    )
    op.create_index('ix_chapter_versions_id', 'chapter_versions', ['id'])


def downgrade() -> None:
    op.drop_table('chapter_versions')
    op.drop_table('chapters')
    op.drop_table('projects')
