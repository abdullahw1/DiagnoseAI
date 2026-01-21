"""Add Patient model and update Case model

Revision ID: 1548dbecdf98
Revises: 5ae3a3be127a
Create Date: 2025-09-25 18:06:40.016156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1548dbecdf98'
down_revision = '5ae3a3be127a'
branch_labels = None
depends_on = None


def upgrade():
    # Create patients table
    op.create_table('patients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.String(length=20), nullable=False),
    sa.Column('first_name', sa.String(length=50), nullable=False),
    sa.Column('last_name', sa.String(length=50), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('gender', sa.String(length=10), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('emergency_contact', sa.String(length=100), nullable=True),
    sa.Column('emergency_phone', sa.String(length=20), nullable=True),
    sa.Column('medical_record_number', sa.String(length=20), nullable=True),
    sa.Column('insurance_info', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_patients_patient_id'), ['patient_id'], unique=True)

    # Add new columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('title', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('department', sa.String(length=100), nullable=True))

    # For existing cases, we'll need to create a default patient first
    # Create a default patient for existing cases
    connection = op.get_bind()
    
    # Check if there are existing cases
    result = connection.execute(sa.text("SELECT COUNT(*) FROM cases")).fetchone()
    if result[0] > 0:
        # Get the first user to assign as creator of default patient
        user_result = connection.execute(sa.text("SELECT id FROM users LIMIT 1")).fetchone()
        if user_result:
            user_id = user_result[0]
            # Insert default patient
            connection.execute(sa.text("""
                INSERT INTO patients (patient_id, first_name, last_name, created_by, created_at, updated_at)
                VALUES ('DEFAULT001', 'Unknown', 'Patient', :user_id, datetime('now'), datetime('now'))
            """), {'user_id': user_id})
            
            # Get the default patient ID
            default_patient_result = connection.execute(sa.text("SELECT id FROM patients WHERE patient_id = 'DEFAULT001'")).fetchone()
            default_patient_id = default_patient_result[0]
        else:
            default_patient_id = 1

    # Add new columns to cases table with default values
    with op.batch_alter_table('cases', schema=None) as batch_op:
        # Add columns with default values first
        batch_op.add_column(sa.Column('case_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('patient_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('study_type', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('body_part', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('indication', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('clinical_history', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('referring_physician', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('study_date', sa.DateTime(), nullable=True))

    # Update existing cases with default values
    if result[0] > 0:
        connection.execute(sa.text("""
            UPDATE cases SET 
                case_number = printf('%06d', id),
                patient_id = :default_patient_id,
                study_type = 'Ultrasound',
                indication = COALESCE(clinical_notes, 'No indication provided'),
                priority = 'routine',
                study_date = created_at
            WHERE case_number IS NULL
        """), {'default_patient_id': default_patient_id})

    # Now make required columns non-nullable and add constraints
    with op.batch_alter_table('cases', schema=None) as batch_op:
        batch_op.alter_column('case_number', nullable=False)
        batch_op.alter_column('patient_id', nullable=False)
        batch_op.create_index(batch_op.f('ix_cases_case_number'), ['case_number'], unique=True)
        batch_op.create_foreign_key('fk_cases_patient_id', 'patients', ['patient_id'], ['id'])
        batch_op.drop_column('clinical_notes')


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('department')
        batch_op.drop_column('title')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')

    with op.batch_alter_table('cases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('clinical_notes', sa.TEXT(), nullable=True))
        batch_op.drop_constraint('fk_cases_patient_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_cases_case_number'))
        batch_op.drop_column('study_date')
        batch_op.drop_column('priority')
        batch_op.drop_column('referring_physician')
        batch_op.drop_column('clinical_history')
        batch_op.drop_column('indication')
        batch_op.drop_column('body_part')
        batch_op.drop_column('study_type')
        batch_op.drop_column('patient_id')
        batch_op.drop_column('case_number')

    with op.batch_alter_table('patients', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_patients_patient_id'))

    op.drop_table('patients')
    # ### end Alembic commands ###
