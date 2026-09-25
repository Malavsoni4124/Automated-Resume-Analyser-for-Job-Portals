from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

def _utcnow():
    return datetime.now(timezone.utc)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # Removing hashed_password from Tenant as users will have it now
    jobs = relationship("Job", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    role = Column(String, default="recruiter") # admin, recruiter
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    
    tenant = relationship("Tenant", back_populates="users")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    title = Column(String)
    raw_text = Column(String)
    parsed_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    tenant = relationship("Tenant", back_populates="jobs")
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    name = Column(String)
    email = Column(String)
    overall_score = Column(Float)
    breakdown = Column(JSON)
    explanation = Column(Text)
    parsed_resume_json = Column(JSON)
    # New columns
    status = Column(String, default="new")          # new | shortlisted | rejected | hired
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    job = relationship("Job", back_populates="candidates")

class CandidateStatusHistory(Base):
    __tablename__ = "candidate_status_history"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    old_status = Column(String)
    new_status = Column(String)
    changed_at = Column(DateTime(timezone=True), default=_utcnow)
