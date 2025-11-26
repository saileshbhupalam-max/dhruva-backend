#!/usr/bin/env python3
"""
Seed ALL departments from government data sources.

This script seeds ALL unique departments found across:
- PGRS Book Keywords (30 departments)
- Officer Performance data (40+ departments)
- Call Center Satisfaction (31 departments)
- Audit Reports (25+ departments)

Auto-generated from: backend/ml/extract_all_departments.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models import Department
from app.config import settings


async def seed_all_departments():
    """Seed all departments found in government data."""

    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
    )

    # Create async session
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    departments = [
        {
            "dept_code": "ACPD",
            "dept_name": "AP Central Power Distribution (CPDCL)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ACPDCL",
            "dept_name": "AP Central Power Distribution Co Ltd (CPDCL)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "AEPDCL",
            "dept_name": "AP Eastern Power Distribution Co Ltd (EPDCL)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SOC_WELF",
            "dept_name": "AP Social Welfare Residential Educational Institutions (APSWREIS)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ASPDCL",
            "dept_name": "AP Southern Power Distribution Co Ltd (SPDCL)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "HOUSING",
            "dept_name": "AP State Housing Corporation Ltd",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "TRANS",
            "dept_name": "AP State Road Transport Corporation (APSRTC)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ASSDC",
            "dept_name": "AP State Skill Development Corporation",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ATAIDC",
            "dept_name": "AP Township And Infrastructure Development Corporation",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "APCRDA",
            "dept_name": "APCRDA",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "AGRI",
            "dept_name": "Agriculture",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "AGRI",
            "dept_name": "Agriculture And Co-operation",
            "name_telugu": "వ్యవసాయం మరియు సహకారం",
            "sla_days": 7,
        },
        {
            "dept_code": "ANI_HUSB",
            "dept_name": "Animal Husbandry",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ANI_HUSB",
            "dept_name": "Animal Husbandry, Dairy Development And Fisheries",
            "name_telugu": "పశుపోషణ, డైరీ అభివృద్ధి మరియు మత్స్య సంపద",
            "sla_days": 7,
        },
        {
            "dept_code": "BC_WELF",
            "dept_name": "Backward Classes",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "BC_WELF",
            "dept_name": "Backward Classes Welfare",
            "name_telugu": "వెనుకబడిన తరగతుల సంక్షేమం",
            "sla_days": 7,
        },
        {
            "dept_code": "CIVIL_SUP",
            "dept_name": "Civil Supplies",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "COOPER",
            "dept_name": "Co-operation",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "CIVIL_SUP",
            "dept_name": "Consumer Affairs, Food And Civil Supplies",
            "name_telugu": "వినియోగదారుల వ్యవహారాలు, ఆహారం మరియు సివిల్ సప్లైస్",
            "sla_days": 7,
        },
        {
            "dept_code": "SKILLS",
            "dept_name": "Department Of Skills Development And Training",
            "name_telugu": "నైపుణ్య అభివృద్ధి మరియు శిక్షణ శాఖ",
            "sla_days": 7,
        },
        {
            "dept_code": "DISASTER",
            "dept_name": "Disaster Management",
            "name_telugu": "విపత్తు నిర్వహణ",
            "sla_days": 7,
        },
        {
            "dept_code": "EDUCATIO",
            "dept_name": "Education",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "TRAIN",
            "dept_name": "Employment and Training",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ENDOW",
            "dept_name": "Endowment",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "ENERGY",
            "dept_name": "Energy",
            "name_telugu": "శక్తి",
            "sla_days": 7,
        },
        {
            "dept_code": "ENVIRON",
            "dept_name": "Environment, Forest, Science And Technology",
            "name_telugu": "పర్యావరణం, అటవీ, విజ్ఞాన శాస్త్ర మరియు సాంకేతికత",
            "sla_days": 7,
        },
        {
            "dept_code": "EXCISE",
            "dept_name": "Excise",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "FAMIWELF",
            "dept_name": "Family Welfare",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "FINANCE",
            "dept_name": "Finance",
            "name_telugu": "ఫైనాన్స్",
            "sla_days": 7,
        },
        {
            "dept_code": "FOREST",
            "dept_name": "Forest",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "GENEADMI",
            "dept_name": "General Administration",
            "name_telugu": "సాధారణ పరిపాలన",
            "sla_days": 7,
        },
        {
            "dept_code": "GVVAVSS",
            "dept_name": "Grama Volunteers/Ward Volunteers And Village Secretariats/Ward Secretariats",
            "name_telugu": "గ్రామ/వార్డు వాలంటీర్లు మరియు గ్రామ/వార్డు సచివాలయాలు",
            "sla_days": 7,
        },
        {
            "dept_code": "HANDLOOM",
            "dept_name": "Handlooms",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "HEALTH",
            "dept_name": "Health",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "HEALTH",
            "dept_name": "Health, Medical And Family Welfare",
            "name_telugu": "ఆరోగ్యం, వైద్యం మరియు కుటుంబ సంక్షేమం",
            "sla_days": 7,
        },
        {
            "dept_code": "HOME",
            "dept_name": "Home (Police)",
            "name_telugu": "హోం (పోలీస్)",
            "sla_days": 7,
        },
        {
            "dept_code": "HOUSING",
            "dept_name": "Housing",
            "name_telugu": "గృహనిర్మాణం",
            "sla_days": 7,
        },
        {
            "dept_code": "HUMARESO",
            "dept_name": "Human Resources (Higher Education)",
            "name_telugu": "మానవ వనరులు (పాఠశాల విద్య)",
            "sla_days": 7,
        },
        {
            "dept_code": "INDUST",
            "dept_name": "Industries",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "INDUST",
            "dept_name": "Industries And Commerce",
            "name_telugu": "పరిశ్రమలు మరియు వాణిజ్యం",
            "sla_days": 7,
        },
        {
            "dept_code": "I&P",
            "dept_name": "Information & PR",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "LABOUR",
            "dept_name": "Labour",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "LABOUR",
            "dept_name": "Labour, Factories, Boilers And Insurance Medical Services",
            "name_telugu": "కార్మిక, కర్మాగారాలు, బాయిలర్లు మరియు బీమా వైద్య సేవలు",
            "sla_days": 7,
        },
        {
            "dept_code": "LAW",
            "dept_name": "Law",
            "name_telugu": "చట్టం",
            "sla_days": 7,
        },
        {
            "dept_code": "LEGAL",
            "dept_name": "Legal",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MARKETIN",
            "dept_name": "Marketing",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MEDIEDUC",
            "dept_name": "Medical Education",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MINES",
            "dept_name": "Mines",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MINOR",
            "dept_name": "Minorities Welfare",
            "name_telugu": "మైనారిటీల సంక్షేమం",
            "sla_days": 7,
        },
        {
            "dept_code": "MINOWELF",
            "dept_name": "Minority Welfare",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MUNICIPA",
            "dept_name": "Municipal",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MUNI",
            "dept_name": "Municipal Administration",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "MUNI",
            "dept_name": "Municipal Administration And Urban Development",
            "name_telugu": "పురపాలక పరిపాలన మరియు పట్టణ అభివృద్ధి",
            "sla_days": 7,
        },
        {
            "dept_code": "PNCHRAJ",
            "dept_name": "Panchayat Raj And Rural Development",
            "name_telugu": "పంచాయతీ రాజ్ మరియు గ్రామీణ అభివృద్ధి",
            "sla_days": 7,
        },
        {
            "dept_code": "PNCHRAJ",
            "dept_name": "Panchayati Raj",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "PNCHRAJ",
            "dept_name": "Panchayati Raj Directorate",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "PNCHRAJ",
            "dept_name": "Panchayati Raj Engineering",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "PLANNING",
            "dept_name": "Planning",
            "name_telugu": "ప్రణాళిక",
            "sla_days": 7,
        },
        {
            "dept_code": "POLICE",
            "dept_name": "Police",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "HEALTH",
            "dept_name": "Public Health",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "REG",
            "dept_name": "Registration and Stamps",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "REG",
            "dept_name": "Registrationand Stamps",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "REVENUE",
            "dept_name": "Revenue (CCLA)",
            "name_telugu": "రెవెన్యూ",
            "sla_days": 7,
        },
        {
            "dept_code": "REVENUE",
            "dept_name": "Revenue Ccla",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "RNB",
            "dept_name": "Roads and Buildings (Ein-C)",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "RURADEVE",
            "dept_name": "Rural Development",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "RWSE",
            "dept_name": "Rural Water Supply Engineering",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SCH_EDU",
            "dept_name": "School Education",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "HEALTH",
            "dept_name": "Secondary Health",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SKILDEVE",
            "dept_name": "Skill Development",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SOC_WELF",
            "dept_name": "Social Welfare",
            "name_telugu": "సామాజిక సంక్షేమం",
            "sla_days": 7,
        },
        {
            "dept_code": "SFEORP",
            "dept_name": "Society For Elimination Of Rural Poverty",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SSLR",
            "dept_name": "Survey Settlements Land Records",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "SSLR",
            "dept_name": "Survey Settlements and Land Records",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "TOURISM",
            "dept_name": "Tourism",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "TRANS",
            "dept_name": "Transport",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "RNB",
            "dept_name": "Transport, Roads And Buildings",
            "name_telugu": "రవాణా, రోడ్లు మరియు భవనాలు",
            "sla_days": 7,
        },
        {
            "dept_code": "TRIBAL",
            "dept_name": "Tribal Welfare",
            "name_telugu": "గిరిజన సంక్షేమం",
            "sla_days": 7,
        },
        {
            "dept_code": "WATER",
            "dept_name": "Water Resources",
            "name_telugu": "జల వనరులు",
            "sla_days": 7,
        },
        {
            "dept_code": "WOMEN",
            "dept_name": "Women & Child",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "WOMEN",
            "dept_name": "Women Development and Child Welfare",
            "name_telugu": None,
            "sla_days": 7,
        },
        {
            "dept_code": "WOMEN",
            "dept_name": "Women, Children, Disabled And Senior Citizens",
            "name_telugu": "మహిళలు, పిల్లలు, వైకల్యులు మరియు వృద్ధులు",
            "sla_days": 7,
        },
        {
            "dept_code": "YATAC",
            "dept_name": "Youth Advancement, Tourism And Culture",
            "name_telugu": "యువజన ఉన్నతి, పర్యాటక మరియు సంస్కృతి",
            "sla_days": 7,
        },
    ]

    async with async_session() as session:
        print(f"Seeding {len(departments)} departments...")

        for dept_data in departments:
            # Check if exists
            from sqlalchemy import select
            stmt = select(Department).where(
                Department.dept_code == dept_data["dept_code"]
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  OK {dept_data['dept_code']} already exists")
            else:
                dept = Department(**dept_data)
                session.add(dept)
                print(f"  + Created {dept_data['dept_code']}: {dept_data['dept_name']}")

        await session.commit()
        print(f"\nOK Seeded {len(departments)} departments successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_all_departments())
