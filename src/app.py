"""
Slalom Capabilities Management System API

A FastAPI application that enables Slalom consultants to register their
capabilities and manage consulting expertise across the organization.
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Session

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "capabilities.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Capability(Base):
    __tablename__ = "capabilities"

    name = Column(String, primary_key=True)
    description = Column(Text, nullable=False)
    practice_area = Column(String, nullable=False)
    skill_levels = Column(Text, nullable=False)   # JSON array
    certifications = Column(Text, nullable=False)  # JSON array
    industry_verticals = Column(Text, nullable=False)  # JSON array
    capacity = Column(Integer, nullable=False)


class Consultant(Base):
    __tablename__ = "consultants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    capability_name = Column(String, nullable=False)
    email = Column(String, nullable=False)


Base.metadata.create_all(engine)

# ---------------------------------------------------------------------------
# Seed data (only inserted when the table is empty)
# ---------------------------------------------------------------------------

SEED_CAPABILITIES = [
    {
        "name": "Cloud Architecture",
        "description": "Design and implement scalable cloud solutions using AWS, Azure, and GCP",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["AWS Solutions Architect", "Azure Architect Expert"],
        "industry_verticals": ["Healthcare", "Financial Services", "Retail"],
        "capacity": 40,
        "consultants": ["alice.smith@slalom.com", "bob.johnson@slalom.com"],
    },
    {
        "name": "Data Analytics",
        "description": "Advanced data analysis, visualization, and machine learning solutions",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Tableau Desktop Specialist", "Power BI Expert", "Google Analytics"],
        "industry_verticals": ["Retail", "Healthcare", "Manufacturing"],
        "capacity": 35,
        "consultants": ["emma.davis@slalom.com", "sophia.wilson@slalom.com"],
    },
    {
        "name": "DevOps Engineering",
        "description": "CI/CD pipeline design, infrastructure automation, and containerization",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Docker Certified Associate", "Kubernetes Admin", "Jenkins Certified"],
        "industry_verticals": ["Technology", "Financial Services"],
        "capacity": 30,
        "consultants": ["john.brown@slalom.com", "olivia.taylor@slalom.com"],
    },
    {
        "name": "Digital Strategy",
        "description": "Digital transformation planning and strategic technology roadmaps",
        "practice_area": "Strategy",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Digital Transformation Certificate", "Agile Certified Practitioner"],
        "industry_verticals": ["Healthcare", "Financial Services", "Government"],
        "capacity": 25,
        "consultants": ["liam.anderson@slalom.com", "noah.martinez@slalom.com"],
    },
    {
        "name": "Change Management",
        "description": "Organizational change leadership and adoption strategies",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Prosci Certified", "Lean Six Sigma Black Belt"],
        "industry_verticals": ["Healthcare", "Manufacturing", "Government"],
        "capacity": 20,
        "consultants": ["ava.garcia@slalom.com", "mia.rodriguez@slalom.com"],
    },
    {
        "name": "UX/UI Design",
        "description": "User experience design and digital product innovation",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Adobe Certified Expert", "Google UX Design Certificate"],
        "industry_verticals": ["Retail", "Healthcare", "Technology"],
        "capacity": 30,
        "consultants": ["amelia.lee@slalom.com", "harper.white@slalom.com"],
    },
    {
        "name": "Cybersecurity",
        "description": "Information security strategy, risk assessment, and compliance",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["CISSP", "CISM", "CompTIA Security+"],
        "industry_verticals": ["Financial Services", "Healthcare", "Government"],
        "capacity": 25,
        "consultants": ["ella.clark@slalom.com", "scarlett.lewis@slalom.com"],
    },
    {
        "name": "Business Intelligence",
        "description": "Enterprise reporting, data warehousing, and business analytics",
        "practice_area": "Technology",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Microsoft BI Certification", "Qlik Sense Certified"],
        "industry_verticals": ["Retail", "Manufacturing", "Financial Services"],
        "capacity": 35,
        "consultants": ["james.walker@slalom.com", "benjamin.hall@slalom.com"],
    },
    {
        "name": "Agile Coaching",
        "description": "Agile transformation and team coaching for scaled delivery",
        "practice_area": "Operations",
        "skill_levels": ["Emerging", "Proficient", "Advanced", "Expert"],
        "certifications": ["Certified Scrum Master", "SAFe Agilist", "ICAgile Certified"],
        "industry_verticals": ["Technology", "Financial Services", "Healthcare"],
        "capacity": 20,
        "consultants": ["charlotte.young@slalom.com", "henry.king@slalom.com"],
    },
]


def _seed():
    with Session(engine) as session:
        if session.query(Capability).count() == 0:
            for cap in SEED_CAPABILITIES:
                session.add(Capability(
                    name=cap["name"],
                    description=cap["description"],
                    practice_area=cap["practice_area"],
                    skill_levels=json.dumps(cap["skill_levels"]),
                    certifications=json.dumps(cap["certifications"]),
                    industry_verticals=json.dumps(cap["industry_verticals"]),
                    capacity=cap["capacity"],
                ))
                for email in cap["consultants"]:
                    session.add(Consultant(capability_name=cap["name"], email=email))
            session.commit()


_seed()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capability_to_dict(cap: Capability, consultants: list[str]) -> dict:
    return {
        "description": cap.description,
        "practice_area": cap.practice_area,
        "skill_levels": json.loads(cap.skill_levels),
        "certifications": json.loads(cap.certifications),
        "industry_verticals": json.loads(cap.industry_verticals),
        "capacity": cap.capacity,
        "consultants": consultants,
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Slalom Capabilities Management API",
    description="API for managing consulting capabilities and consultant expertise",
)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/capabilities")
def get_capabilities():
    with Session(engine) as session:
        caps = session.query(Capability).all()
        result = {}
        for cap in caps:
            emails = [
                c.email
                for c in session.query(Consultant)
                .filter(Consultant.capability_name == cap.name)
                .all()
            ]
            result[cap.name] = _capability_to_dict(cap, emails)
        return result


@app.post("/capabilities/{capability_name}/register")
def register_for_capability(capability_name: str, email: str):
    """Register a consultant for a capability"""
    with Session(engine) as session:
        cap = session.get(Capability, capability_name)
        if cap is None:
            raise HTTPException(status_code=404, detail="Capability not found")

        already = (
            session.query(Consultant)
            .filter(
                Consultant.capability_name == capability_name,
                Consultant.email == email,
            )
            .first()
        )
        if already:
            raise HTTPException(
                status_code=400,
                detail="Consultant is already registered for this capability",
            )

        session.add(Consultant(capability_name=capability_name, email=email))
        session.commit()
    return {"message": f"Registered {email} for {capability_name}"}


@app.delete("/capabilities/{capability_name}/unregister")
def unregister_from_capability(capability_name: str, email: str):
    """Unregister a consultant from a capability"""
    with Session(engine) as session:
        cap = session.get(Capability, capability_name)
        if cap is None:
            raise HTTPException(status_code=404, detail="Capability not found")

        row = (
            session.query(Consultant)
            .filter(
                Consultant.capability_name == capability_name,
                Consultant.email == email,
            )
            .first()
        )
        if row is None:
            raise HTTPException(
                status_code=400,
                detail="Consultant is not registered for this capability",
            )

        session.delete(row)
        session.commit()
    return {"message": f"Unregistered {email} from {capability_name}"}
