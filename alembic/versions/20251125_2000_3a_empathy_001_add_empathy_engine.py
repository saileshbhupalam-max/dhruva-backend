"""Add empathy engine tables

Revision ID: 3a_empathy_001
Revises: 3b_grievance_fields
Create Date: 2025-11-25 20:00:00.000000+05:30

Creates tables for the Empathy Engine:
- empathy_templates: Pre-written compassionate responses
- distress_keywords: Keywords to detect distress levels
- grievance_sentiment: Analysis results per grievance
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3a_empathy_001'
down_revision: Union[str, None] = '3b_grievance_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create empathy engine tables and seed data."""
    # Create empathy_templates table
    op.create_table(
        'empathy_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('template_key', sa.String(50), unique=True, nullable=False),
        sa.Column('distress_level', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('placeholders', postgresql.JSONB(), server_default='{}'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name='ck_empathy_templates_distress_level'
        ),
        sa.CheckConstraint(
            "language IN ('te', 'en', 'hi')",
            name='ck_empathy_templates_language'
        )
    )
    op.create_index(
        'idx_empathy_templates_lookup',
        'empathy_templates',
        ['distress_level', 'category', 'language'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Create distress_keywords table
    op.create_table(
        'distress_keywords',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('keyword', sa.String(100), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('distress_level', sa.String(20), nullable=False),
        sa.Column('weight', sa.Numeric(3, 2), server_default='1.00'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('keyword', 'language', name='uq_distress_keyword_lang'),
        sa.CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name='ck_distress_keywords_level'
        ),
        sa.CheckConstraint(
            "language IN ('te', 'en', 'hi')",
            name='ck_distress_keywords_language'
        ),
        sa.CheckConstraint(
            'weight >= 0.00 AND weight <= 2.00',
            name='ck_distress_keywords_weight'
        )
    )
    op.create_index(
        'idx_distress_keywords_lookup',
        'distress_keywords',
        ['language', 'keyword'],
        postgresql_where=sa.text('is_active = TRUE')
    )

    # Create grievance_sentiment table
    op.create_table(
        'grievance_sentiment',
        sa.Column('grievance_id', sa.String(50), primary_key=True),
        sa.Column('distress_score', sa.Numeric(4, 2), nullable=True),
        sa.Column('distress_level', sa.String(20), nullable=False),
        sa.Column('detected_keywords', postgresql.JSONB(), server_default='[]'),
        sa.Column('empathy_template_used', sa.String(50), nullable=True),
        sa.Column('original_sla_days', sa.Integer(), nullable=False),
        sa.Column('adjusted_sla_days', sa.Integer(), nullable=False),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['grievance_id'], ['grievances.grievance_id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            'distress_score >= 0.00 AND distress_score <= 10.00',
            name='ck_grievance_sentiment_score'
        ),
        sa.CheckConstraint(
            "distress_level IN ('CRITICAL', 'HIGH', 'MEDIUM', 'NORMAL')",
            name='ck_grievance_sentiment_level'
        )
    )
    op.create_index(
        'idx_grievance_sentiment_level',
        'grievance_sentiment',
        ['distress_level', 'analyzed_at']
    )

    # Seed distress keywords
    op.execute("""
        INSERT INTO distress_keywords (keyword, language, distress_level, weight) VALUES
        -- CRITICAL Telugu
        ('చనిపోతున్న', 'te', 'CRITICAL', 1.50),
        ('ఆకలి', 'te', 'CRITICAL', 1.50),
        ('రక్తం', 'te', 'CRITICAL', 1.50),
        ('ఆసుపత్రి', 'te', 'CRITICAL', 1.30),
        ('అత్యవసర', 'te', 'CRITICAL', 1.50),
        ('చావు', 'te', 'CRITICAL', 1.50),
        ('ప్రాణాంతక', 'te', 'CRITICAL', 1.50),
        -- CRITICAL English
        ('dying', 'en', 'CRITICAL', 1.50),
        ('starving', 'en', 'CRITICAL', 1.50),
        ('blood', 'en', 'CRITICAL', 1.30),
        ('hospital', 'en', 'CRITICAL', 1.30),
        ('emergency', 'en', 'CRITICAL', 1.50),
        ('death', 'en', 'CRITICAL', 1.50),
        ('life-threatening', 'en', 'CRITICAL', 1.50),
        -- HIGH Telugu
        ('నెలలు', 'te', 'HIGH', 1.20),
        ('ఆపేసారు', 'te', 'HIGH', 1.30),
        ('తిరస్కరించారు', 'te', 'HIGH', 1.20),
        ('ఎక్కడికి వెళ్ళాలి', 'te', 'HIGH', 1.10),
        ('నిరాశ', 'te', 'HIGH', 1.20),
        -- HIGH English
        ('months', 'en', 'HIGH', 1.20),
        ('stopped', 'en', 'HIGH', 1.30),
        ('rejected', 'en', 'HIGH', 1.20),
        ('where to go', 'en', 'HIGH', 1.10),
        ('desperate', 'en', 'HIGH', 1.20),
        -- MEDIUM Telugu
        ('ఆలస్యం', 'te', 'MEDIUM', 1.00),
        ('రాలేదు', 'te', 'MEDIUM', 1.00),
        ('సమస్య', 'te', 'MEDIUM', 1.00),
        ('కష్టం', 'te', 'MEDIUM', 1.00),
        -- MEDIUM English
        ('delay', 'en', 'MEDIUM', 1.00),
        ('not received', 'en', 'MEDIUM', 1.00),
        ('problem', 'en', 'MEDIUM', 1.00),
        ('difficult', 'en', 'MEDIUM', 1.00),
        -- NORMAL Telugu
        ('కావాలి', 'te', 'NORMAL', 0.80),
        ('అభ్యర్థన', 'te', 'NORMAL', 0.80),
        ('సమాచారం', 'te', 'NORMAL', 0.80),
        -- NORMAL English
        ('need', 'en', 'NORMAL', 0.80),
        ('request', 'en', 'NORMAL', 0.80),
        ('information', 'en', 'NORMAL', 0.80),
        -- CRITICAL Hindi
        ('मर रहे', 'hi', 'CRITICAL', 1.50),
        ('भूखे', 'hi', 'CRITICAL', 1.50),
        ('खून', 'hi', 'CRITICAL', 1.30),
        ('अस्पताल', 'hi', 'CRITICAL', 1.30),
        ('आपातकालीन', 'hi', 'CRITICAL', 1.50),
        ('मौत', 'hi', 'CRITICAL', 1.50),
        -- HIGH Hindi
        ('महीने', 'hi', 'HIGH', 1.20),
        ('बंद कर दिया', 'hi', 'HIGH', 1.30),
        ('अस्वीकार', 'hi', 'HIGH', 1.20),
        ('निराश', 'hi', 'HIGH', 1.20),
        -- MEDIUM Hindi
        ('देरी', 'hi', 'MEDIUM', 1.00),
        ('नहीं मिला', 'hi', 'MEDIUM', 1.00),
        ('समस्या', 'hi', 'MEDIUM', 1.00),
        -- NORMAL Hindi
        ('चाहिए', 'hi', 'NORMAL', 0.80),
        ('अनुरोध', 'hi', 'NORMAL', 0.80),
        -- AP WELFARE SCHEME SPECIFIC KEYWORDS (Telugu)
        ('పింఛను రాలేదు', 'te', 'HIGH', 1.30),
        ('వృద్ధాప్య పింఛను', 'te', 'MEDIUM', 1.10),
        ('విధవ పింఛను', 'te', 'MEDIUM', 1.10),
        ('వికలాంగ పింఛను', 'te', 'MEDIUM', 1.10),
        ('పింఛను ఆగిపోయింది', 'te', 'HIGH', 1.30),
        ('పింఛను డబ్బులు', 'te', 'MEDIUM', 1.00),
        ('అమ్మ వొడి', 'te', 'MEDIUM', 1.00),
        ('అమ్మ వొడి రాలేదు', 'te', 'HIGH', 1.20),
        ('పిల్లల చదువు', 'te', 'MEDIUM', 1.00),
        ('స్కూల్ ఫీజు', 'te', 'MEDIUM', 1.00),
        ('విద్యా దీవెన', 'te', 'MEDIUM', 1.00),
        ('కాలేజీ ఫీజు', 'te', 'MEDIUM', 1.00),
        ('ఫీజు రీయంబర్స్‌మెంట్', 'te', 'MEDIUM', 1.00),
        ('రైతు భరోసా', 'te', 'MEDIUM', 1.00),
        ('రైతు భరోసా రాలేదు', 'te', 'HIGH', 1.20),
        ('పంట నష్టం', 'te', 'HIGH', 1.30),
        ('వ్యవసాయ రుణం', 'te', 'MEDIUM', 1.10),
        ('ఇల్లు లేదు', 'te', 'HIGH', 1.30),
        ('పెదలందరికీ ఇళ్లు', 'te', 'MEDIUM', 1.00),
        ('హౌసింగ్', 'te', 'MEDIUM', 1.00),
        ('ఇంటి పట్టా', 'te', 'MEDIUM', 1.00),
        ('రేషన్ కార్డు', 'te', 'MEDIUM', 1.00),
        ('రేషన్ రాలేదు', 'te', 'HIGH', 1.20),
        ('బియ్యం రాలేదు', 'te', 'HIGH', 1.20),
        ('డీలర్ ఇవ్వలేదు', 'te', 'HIGH', 1.20),
        ('భూమి సమస్య', 'te', 'MEDIUM', 1.00),
        ('పట్టా లేదు', 'te', 'MEDIUM', 1.10),
        ('సర్వే నంబర్', 'te', 'NORMAL', 0.90),
        ('ఆక్రమణ', 'te', 'HIGH', 1.20),
        ('కుల ధృవీకరణ', 'te', 'MEDIUM', 1.00),
        ('కుల సర్టిఫికేట్', 'te', 'MEDIUM', 1.00),
        ('BC సర్టిఫికేట్', 'te', 'MEDIUM', 1.00),
        ('SC సర్టిఫికేట్', 'te', 'MEDIUM', 1.00),
        ('ST సర్టిఫికేట్', 'te', 'MEDIUM', 1.00),
        ('నీళ్లు రావడం లేదు', 'te', 'HIGH', 1.20),
        ('కరెంట్ లేదు', 'te', 'HIGH', 1.20),
        ('బిల్లు ఎక్కువ', 'te', 'MEDIUM', 1.00),
        ('ఆరోగ్య శ్రీ', 'te', 'MEDIUM', 1.00),
        ('ఆసుపత్రిలో చేర్చుకోలేదు', 'te', 'CRITICAL', 1.40),
        ('వైద్యం దొరకడం లేదు', 'te', 'HIGH', 1.30),
        -- ROMANIZED TELUGU
        ('pension raaledu', 'te', 'HIGH', 1.20),
        ('ration raaledu', 'te', 'HIGH', 1.20),
        ('amma vodi raaledu', 'te', 'HIGH', 1.20),
        ('illu ledu', 'te', 'HIGH', 1.20),
        ('neellu raavadam ledu', 'te', 'HIGH', 1.20),
        ('current ledu', 'te', 'HIGH', 1.20),
        ('dabbu raaledu', 'te', 'HIGH', 1.20),
        ('help kavali', 'te', 'MEDIUM', 1.00),
        ('samasyaa', 'te', 'MEDIUM', 1.00),
        -- MIXED TELUGU-ENGLISH
        ('pension aagipoyindi', 'te', 'HIGH', 1.30),
        ('ration card ledu', 'te', 'MEDIUM', 1.10),
        ('hospital lo admit cheyaledu', 'te', 'CRITICAL', 1.40),
        ('officer garu help cheyaledu', 'te', 'HIGH', 1.20),
        ('application reject chesaru', 'te', 'HIGH', 1.20);
    """)

    # Seed empathy templates
    op.execute("""
        INSERT INTO empathy_templates (template_key, distress_level, category, language, template_text, placeholders) VALUES
        -- CRITICAL Generic Telugu
        ('critical_generic_te', 'CRITICAL', NULL, 'te',
        'మీ కష్టాలు మాకు అర్థమవుతున్నాయి.
మీ కేసు అత్యవసరంగా గుర్తించబడింది.

Case ID: {case_id}
Priority: అత్యవసరం
24 గంటల్లో మీకు అప్‌డేట్ వస్తుంది.

మీరు ఒంటరిగా లేరు - మేము మీకు సహాయం చేస్తాము.',
        '{"case_id": true}'::jsonb),

        -- CRITICAL Generic English
        ('critical_generic_en', 'CRITICAL', NULL, 'en',
        'We understand your hardship.
Your case has been marked as URGENT.

Case ID: {case_id}
Priority: URGENT
You will receive an update within 24 hours.

You are not alone - we will help you.',
        '{"case_id": true}'::jsonb),

        -- CRITICAL Pension Telugu
        ('critical_pension_te', 'CRITICAL', 'Pension', 'te',
        'మీ పెన్షన్ సమస్య గురించి మాకు బాధగా ఉంది.
మీ కేసు అత్యవసరంగా గుర్తించబడింది.

Case ID: {case_id}
Department: {department}
Priority: అత్యవసరం

24 గంటల్లో మీ పెన్షన్ విషయంలో చర్య తీసుకుంటాము.
మీరు ఒంటరిగా లేరు.',
        '{"case_id": true, "department": true}'::jsonb),

        -- HIGH Generic Telugu
        ('high_generic_te', 'HIGH', NULL, 'te',
        'మీ సమస్య మాకు అందింది.
మీ కేసు ప్రాధాన్యతగా గుర్తించబడింది.

Case ID: {case_id}
Priority: అధిక ప్రాధాన్యత
3 రోజుల్లో మీకు అప్‌డేట్ వస్తుంది.

మేము మీకు సహాయం చేస్తాము.',
        '{"case_id": true}'::jsonb),

        -- HIGH Generic English
        ('high_generic_en', 'HIGH', NULL, 'en',
        'We have received your concern.
Your case has been marked as HIGH priority.

Case ID: {case_id}
Priority: HIGH
You will receive an update within 3 days.

We will help you.',
        '{"case_id": true}'::jsonb),

        -- MEDIUM Generic Telugu
        ('medium_generic_te', 'MEDIUM', NULL, 'te',
        'మీ సమస్య మాకు అందింది.

Case ID: {case_id}
Department: {department}
Expected Resolution: 7 రోజులు

మేము మీకు సహాయం చేస్తాము.',
        '{"case_id": true, "department": true}'::jsonb),

        -- MEDIUM Generic English
        ('medium_generic_en', 'MEDIUM', NULL, 'en',
        'We have received your issue.

Case ID: {case_id}
Department: {department}
Expected Resolution: 7 days

We will help you.',
        '{"case_id": true, "department": true}'::jsonb),

        -- NORMAL Generic Telugu
        ('normal_generic_te', 'NORMAL', NULL, 'te',
        'మీ అభ్యర్థన మాకు అందింది.

Case ID: {case_id}
Department: {department}
Expected Resolution: 30 రోజులు

ధన్యవాదాలు.',
        '{"case_id": true, "department": true}'::jsonb),

        -- NORMAL Generic English
        ('normal_generic_en', 'NORMAL', NULL, 'en',
        'Your request has been received.

Case ID: {case_id}
Department: {department}
Expected Resolution: 30 days

Thank you.',
        '{"case_id": true, "department": true}'::jsonb),

        -- CRITICAL Generic Hindi
        ('critical_generic_hi', 'CRITICAL', NULL, 'hi',
        'हम आपकी कठिनाई समझते हैं।
आपका केस तत्काल के रूप में चिह्नित किया गया है।

Case ID: {case_id}
Priority: तत्काल
24 घंटे में आपको अपडेट मिलेगा।

आप अकेले नहीं हैं - हम आपकी मदद करेंगे।',
        '{"case_id": true}'::jsonb),

        -- HIGH Generic Hindi
        ('high_generic_hi', 'HIGH', NULL, 'hi',
        'आपकी समस्या हमें मिल गई है।
आपका केस उच्च प्राथमिकता के रूप में चिह्नित किया गया है।

Case ID: {case_id}
Priority: उच्च प्राथमिकता
3 दिनों में आपको अपडेट मिलेगा।

हम आपकी मदद करेंगे।',
        '{"case_id": true}'::jsonb),

        -- MEDIUM Generic Hindi
        ('medium_generic_hi', 'MEDIUM', NULL, 'hi',
        'आपकी समस्या हमें मिल गई है।

Case ID: {case_id}
Department: {department}
Expected Resolution: 7 दिन

हम आपकी मदद करेंगे।',
        '{"case_id": true, "department": true}'::jsonb),

        -- NORMAL Generic Hindi
        ('normal_generic_hi', 'NORMAL', NULL, 'hi',
        'आपका अनुरोध प्राप्त हो गया है।

Case ID: {case_id}
Department: {department}
Expected Resolution: 30 दिन

धन्यवाद।',
        '{"case_id": true, "department": true}'::jsonb);
    """)


def downgrade() -> None:
    """Drop empathy engine tables."""
    op.drop_table('grievance_sentiment')
    op.drop_table('distress_keywords')
    op.drop_table('empathy_templates')
