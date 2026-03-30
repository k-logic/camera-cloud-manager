"""add_audio_settings

Revision ID: d1a2b3c4e5f6
Revises: af4a1369067c
Create Date: 2026-03-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1a2b3c4e5f6'
down_revision: Union[str, None] = 'af4a1369067c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('camera_settings', sa.Column('audio_bitrate', sa.String(length=20), nullable=False, server_default='128k'))
    op.add_column('camera_settings', sa.Column('audio_sample_rate', sa.Integer(), nullable=False, server_default='44100'))
    op.add_column('camera_settings', sa.Column('audio_channels', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('camera_settings', 'audio_channels')
    op.drop_column('camera_settings', 'audio_sample_rate')
    op.drop_column('camera_settings', 'audio_bitrate')
