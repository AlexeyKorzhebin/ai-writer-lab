"""add narrative spec tables and project.max_iterations

Revision ID: a1b2c3d4e5f6
Revises: 7e33e9dfac5f
Create Date: 2026-03-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7e33e9dfac5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('max_iterations', sa.Integer(), nullable=True, server_default='3'))

    op.create_table(
        'narrative_specs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=False, unique=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('logline', sa.Text(), nullable=True),
        sa.Column('genre', sa.String(50), nullable=True, server_default='literary_fiction'),
        sa.Column('tone', sa.Text(), nullable=True),
        sa.Column('themes', sa.JSON(), nullable=True),
        sa.Column('central_conflict', sa.Text(), nullable=True),
        sa.Column('story_format', sa.String(100), nullable=True),
        sa.Column('world_type', sa.String(100), nullable=True, server_default='realistic'),
        sa.Column('world_rules', sa.Text(), nullable=True),
        sa.Column('world_time_period', sa.String(255), nullable=True),
        sa.Column('world_power_structures', sa.Text(), nullable=True),
        sa.Column('world_atmosphere', sa.Text(), nullable=True),
        sa.Column('macro_structure', sa.String(50), nullable=True, server_default='three_act'),
        sa.Column('turning_points', sa.JSON(), nullable=True),
        sa.Column('climax', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
    )
    op.create_index('ix_narrative_specs_id', 'narrative_specs', ['id'])

    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('narrative_spec_id', sa.Integer(), sa.ForeignKey('narrative_specs.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=True, server_default='supporting'),
        sa.Column('motivation', sa.Text(), nullable=True),
        sa.Column('fear', sa.Text(), nullable=True),
        sa.Column('secret', sa.Text(), nullable=True),
        sa.Column('relationships', sa.JSON(), nullable=True),
        sa.Column('arc_start_state', sa.Text(), nullable=True),
        sa.Column('arc_inner_conflict', sa.Text(), nullable=True),
        sa.Column('arc_key_events', sa.JSON(), nullable=True),
        sa.Column('arc_turning_point', sa.Text(), nullable=True),
        sa.Column('arc_end_state', sa.Text(), nullable=True),
    )
    op.create_index('ix_characters_id', 'characters', ['id'])

    op.create_table(
        'scenes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('narrative_spec_id', sa.Integer(), sa.ForeignKey('narrative_specs.id'), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('participants', sa.JSON(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('emotional_state', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
    )
    op.create_index('ix_scenes_id', 'scenes', ['id'])


def downgrade() -> None:
    op.drop_table('scenes')
    op.drop_table('characters')
    op.drop_table('narrative_specs')
    op.drop_column('projects', 'max_iterations')
