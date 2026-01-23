"""Create salon booking system tables

Revision ID: 001_initial
Revises:
Create Date: 2026-01-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types only if they don't exist
    try:
        # Try to create userroleenum
        op.execute("CREATE TYPE userroleenum AS ENUM ('CLIENT', 'MASTER', 'ADMIN')")
    except Exception:
        # Type already exists, continue
        pass
    
    try:
        # Try to create appointmentstatusenum
        op.execute("CREATE TYPE appointmentstatusenum AS ENUM ('BOOKED', 'CANCELLED', 'COMPLETED')")
    except Exception:
        # Type already exists, continue
        pass

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('CLIENT', 'MASTER', 'ADMIN', name='userroleenum', create_type=False), nullable=False, server_default='CLIENT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )

    # Create salons table
    op.create_table(
        'salons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('gis_link', sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create services table
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['salon_id'], ['salons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create masters table
    op.create_table(
        'masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['salon_id'], ['salons.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create master_services junction table
    op.create_table(
        'master_services',
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('master_id', 'service_id')
    )

    # Create master_schedules table
    op.create_table(
        'master_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('time_from', sa.Time(), nullable=False),
        sa.Column('time_to', sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.BigInteger(), nullable=False),
        sa.Column('salon_id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time_start', sa.Time(), nullable=False),
        sa.Column('time_end', sa.Time(), nullable=False),
        sa.Column('status', postgresql.ENUM('BOOKED', 'CANCELLED', 'COMPLETED', name='appointmentstatusenum', create_type=False), nullable=False, server_default='BOOKED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['client_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.ForeignKeyConstraint(['salon_id'], ['salons.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index('ix_appointments_client_id', 'appointments', ['client_id'])
    op.create_index('ix_appointments_master_id', 'appointments', ['master_id'])
    op.create_index('ix_appointments_date', 'appointments', ['date'])
    op.create_index('ix_appointments_status', 'appointments', ['status'])
    op.create_index('ix_master_schedules_master_id', 'master_schedules', ['master_id'])
    op.create_index('ix_masters_user_id', 'masters', ['user_id'])
    op.create_index('ix_services_salon_id', 'services', ['salon_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_services_salon_id', table_name='services')
    op.drop_index('ix_masters_user_id', table_name='masters')
    op.drop_index('ix_master_schedules_master_id', table_name='master_schedules')
    op.drop_index('ix_appointments_status', table_name='appointments')
    op.drop_index('ix_appointments_date', table_name='appointments')
    op.drop_index('ix_appointments_master_id', table_name='appointments')
    op.drop_index('ix_appointments_client_id', table_name='appointments')

    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('appointments')
    op.drop_table('master_schedules')
    op.drop_table('master_services')
    op.drop_table('masters')
    op.drop_table('services')
    op.drop_table('salons')
    op.drop_table('users')

    # Drop enums
    sa.Enum(name='appointmentstatusenum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userroleenum').drop(op.get_bind(), checkfirst=True)