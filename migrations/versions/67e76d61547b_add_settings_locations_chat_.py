"""add_settings_locations_chat_illustrations

Revision ID: 67e76d61547b
Revises: a1b2c3d4e5f6
Create Date: 2026-03-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '67e76d61547b'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'settings',
        sa.Column('key', sa.String(255), primary_key=True),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('encrypted', sa.Boolean, default=False),
    )

    op.create_table(
        'locations',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_type', sa.String(50), default='building'),
        sa.Column('parent_id', sa.Integer, sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('visual_details', sa.Text, nullable=True),
        sa.Column('atmosphere', sa.Text, nullable=True),
        sa.Column('significance', sa.Text, nullable=True),
        sa.Column('climate', sa.Text, nullable=True),
        sa.Column('inhabitants', sa.Text, nullable=True),
        sa.Column('notable_features', sa.Text, nullable=True),
        sa.Column('connected_to', sa.JSON, nullable=True),
        sa.Column('travel_notes', sa.Text, nullable=True),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('first_appearance', sa.Integer, nullable=True),
    )

    op.create_table(
        'location_states',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('location_id', sa.Integer, sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('after_scene', sa.Integer, nullable=True),
        sa.Column('description_override', sa.Text, nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
    )

    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('task_name', sa.String(255), default='Общий чат'),
        sa.Column('pinned_context', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )

    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('session_id', sa.Integer, sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('references', sa.JSON, nullable=True),
        sa.Column('tokens', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )

    op.create_table(
        'illustration_prompts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('scene_index', sa.Integer, nullable=True),
        sa.Column('template', sa.String(100), nullable=True),
        sa.Column('prompt_text', sa.Text, nullable=True),
        sa.Column('variant_data', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
    )

    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime, nullable=True))

    with op.batch_alter_table('scenes') as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('time_context', sa.JSON, nullable=True))

    with op.batch_alter_table('characters') as batch_op:
        batch_op.add_column(sa.Column('appearance', sa.Text, nullable=True))
        batch_op.add_column(sa.Column('speech_style', sa.Text, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('characters') as batch_op:
        batch_op.drop_column('speech_style')
        batch_op.drop_column('appearance')

    with op.batch_alter_table('scenes') as batch_op:
        batch_op.drop_column('time_context')
        batch_op.drop_column('location')

    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_column('created_at')

    op.drop_table('illustration_prompts')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('location_states')
    op.drop_table('locations')
    op.drop_table('settings')
