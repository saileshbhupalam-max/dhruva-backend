"""Setup script for installing the DHRUVA-PGRS backend package."""

from setuptools import find_packages, setup

setup(
    name="dhruva-pgrs",
    version="1.0.0",
    description="DHRUVA-PGRS Backend - Public Grievance Redressal System",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "sqlalchemy==2.0.23",
        "asyncpg==0.29.0",
        "alembic==1.13.0",
        "pydantic==2.5.0",
        "pydantic-settings==2.1.0",
        "python-dotenv==1.0.0",
    ],
    extras_require={
        "dev": [
            "mypy==1.7.1",
            "types-sqlalchemy==1.4.53.38",
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "pytest-cov==4.1.0",
            "black==23.11.0",
            "flake8==6.1.0",
        ],
    },
)
