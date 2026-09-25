import os
import io
import csv
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from datetime import timedelta

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

from src.database.session import get_db
from src.database.models import Tenant, Job, Candidate, CandidateStatusHistory, User
from src.api.dependencies import get_resume_parser, get_matching_engine, get_jd_parser
from src.schema import JobDescriptionSchema, ResumeSchema
from src.matching.explainer import MatchExplainer
from src.extractors.web_scraper import GitHubScraper
from src.api.auth import (
    get_current_tenant, get_current_user, get_password_hash, verify_password,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
VALID_STATUSES = {"new", "shortlisted", "rejected", "hired"}

# ─────────────────────────────────────────
#  Request / Response Schemas
# ─────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str
    password: str

class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str

class JobCreate(BaseModel):
    title: str
    raw_text: Optional[str] = ""
    skills: Optional[List[str]] = None
    min_experience_years: Optional[float] = None
    degree_required: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    raw_text: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience_years: Optional[float] = None
    degree_required: Optional[str] = None

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    title: str
    parsed_json: Dict[str, Any]

class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    overall_score: float
    explanation: str
    breakdown: Optional[Dict[str, Any]] = None
    parsed_resume_json: Optional[Dict[str, Any]] = None
    status: Optional[str] = "new"
    notes: Optional[str] = ""

class CandidateStatusUpdate(BaseModel):
    status: str

class CandidateNotesUpdate(BaseModel):
    notes: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_jobs: int
    total_candidates: int
    avg_score: float
    shortlisted_count: int
    hired_count: int
    rejected_count: int
    top_candidates: List[Dict[str, Any]]
    score_distribution: List[Dict[str, Any]]
    skills_gap: List[Dict[str, Any]]
    time_to_hire_days: Optional[float] = 0.0
    pass_through_rate: Optional[float] = 0.0

# ─────────────────────────────────────────
#  Auth
# ─────────────────────────────────────────

@router.post("/tenants/", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, db: AsyncSession = Depends(get_db)):
    db_tenant = Tenant(name=tenant.name)
    db.add(db_tenant)
    await db.flush()
    slug = tenant.name.lower().replace(" ", "")
    email = f"admin@{slug}.com"
    db_user = User(email=email, hashed_password=get_password_hash(tenant.password), name="Admin", role="admin", tenant_id=db_tenant.id)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_tenant)
    return db_tenant

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role}

# ─────────────────────────────────────────
#  Jobs
# ─────────────────────────────────────────

@router.get("/jobs/", response_model=List[JobResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Job).where(Job.tenant_id == current_tenant.id).order_by(Job.id.desc())
    )
    jobs = result.scalars().all()
    # Normalize parsed_json skills key for older records
    for job in jobs:
        if job.parsed_json and "required_skills" in job.parsed_json and "skills" not in job.parsed_json:
            job.parsed_json["skills"] = job.parsed_json.pop("required_skills")
    return jobs

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.parsed_json and "required_skills" in job.parsed_json:
        job.parsed_json["skills"] = job.parsed_json.pop("required_skills")
    return job

@router.post("/jobs/", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    jd_parser=Depends(get_jd_parser),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    raw_text = job.raw_text or ""
    parsed_dict = {}
    if raw_text.strip():
        parsed_jd = jd_parser.parse(raw_text)
        parsed_dict = parsed_jd.model_dump()
    else:
        parsed_dict = {
            "title": job.title,
            "skills": [],
            "min_experience_years": 0.0,
            "degree_required": "None",
            "key_responsibilities": []
        }
    
    # Standardize skills key if parser returned required_skills
    if "required_skills" in parsed_dict and "skills" not in parsed_dict:
        parsed_dict["skills"] = parsed_dict.pop("required_skills")

    # Override or append explicitly provided fields
    if job.skills is not None:
        explicit = [s.strip() for s in job.skills if s and s.strip()]
        if explicit:
            parsed_dict["skills"] = explicit
    if job.min_experience_years is not None:
        parsed_dict["min_experience_years"] = job.min_experience_years
    if job.degree_required is not None:
        parsed_dict["degree_required"] = job.degree_required

    db_job = Job(
        tenant_id=current_tenant.id,
        title=job.title,
        raw_text=raw_text,
        parsed_json=parsed_dict
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job

@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job_update.title is not None:
        job.title = job_update.title
    if job_update.raw_text is not None:
        job.raw_text = job_update.raw_text
    
    parsed = dict(job.parsed_json or {})
    if "required_skills" in parsed and "skills" not in parsed:
        parsed["skills"] = parsed.pop("required_skills")
        
    if job_update.skills is not None:
        parsed["skills"] = [s.strip() for s in job_update.skills if s and s.strip()]
    if job_update.min_experience_years is not None:
        parsed["min_experience_years"] = job_update.min_experience_years
    if job_update.degree_required is not None:
        parsed["degree_required"] = job_update.degree_required

    job.parsed_json = parsed
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(job, "parsed_json")

    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()

# ─────────────────────────────────────────
#  Candidates
# ─────────────────────────────────────────

@router.post("/jobs/{job_id}/candidates/upload", status_code=202)
async def upload_resume(
    job_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
    parser=Depends(get_resume_parser),
    matching_engine=Depends(get_matching_engine)
):
    # Verify job ownership
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    db_job = result.scalar_one_or_none()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate file type
    filename = file.filename or "resume.pdf"
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ".pdf"
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: PDF, DOCX, DOC, TXT"
        )

    # Read file content and validate size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB}MB."
        )

    # Save to temp file
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(file_content)

    # Try Celery, fall back to inline processing
    try:
        from src.worker.tasks import process_resume_task
        task = process_resume_task.delay(job_id, path)
        return {"task_id": task.id, "status": "processing"}
    except Exception as e:
        print(f"Celery unavailable ({type(e).__name__}), processing inline...")

    try:
        parse_output = parser.parse(path)
        resume_data = parse_output.data if (parse_output and parse_output.data) else ResumeSchema()

        # Normalize JD schema
        jd_dict = dict(db_job.parsed_json)
        if "required_skills" in jd_dict and "skills" not in jd_dict:
            jd_dict["skills"] = jd_dict.pop("required_skills")
        jd_schema = JobDescriptionSchema(**jd_dict)

        match_result = matching_engine.calculate_match(jd_schema, resume_data)
        explanation = MatchExplainer.explain(match_result, jd_schema, resume_data)

        contact = getattr(resume_data, "contact", None)
        name = (contact.name if contact and contact.name else None) or filename
        email = (contact.email if contact and contact.email else None) or "candidate@example.com"

        # Duplicate detection: check if this email already applied to this job
        if email and email != "candidate@example.com":
            dup_res = await db.execute(
                select(Candidate).where(Candidate.job_id == job_id, Candidate.email == email)
            )
            existing = dup_res.scalar_one_or_none()
            if existing:
                return {
                    "task_id": f"dup_{existing.id}",
                    "status": "DUPLICATE",
                    "candidate_id": existing.id,
                    "message": f"A candidate with email '{email}' already exists for this job. Updated their score.",
                    "duplicate": True
                }

        candidate = Candidate(
            job_id=job_id,
            name=name,
            email=email,
            overall_score=match_result["overall_score"],
            breakdown=match_result["breakdown"],
            explanation=explanation,
            parsed_resume_json=resume_data.model_dump(),
            status="new",
            notes=""
        )
        db.add(candidate)
        await db.commit()
        await db.refresh(candidate)
        return {"task_id": f"sync_{candidate.id}", "status": "SUCCESS", "candidate_id": candidate.id}
    finally:
        if os.path.exists(path):
            os.remove(path)

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_tenant: Tenant = Depends(get_current_tenant)
):
    if task_id.startswith("sync_"):
        return {"task_id": task_id, "status": "SUCCESS"}
    try:
        from celery.result import AsyncResult
        from src.worker.celery_app import celery_app
        r = AsyncResult(task_id, app=celery_app)
        return {"task_id": task_id, "status": r.status, "result": r.result if r.ready() else None}
    except Exception:
        return {"task_id": task_id, "status": "SUCCESS"}

class GitHubImportRequest(BaseModel):
    job_id: int
    github_url: str

@router.post("/candidates/from-github")
async def import_from_github(
    body: GitHubImportRequest,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
    engine = Depends(get_matching_engine)
):
    # Check job
    res = await db.execute(select(Job).where(Job.id == body.job_id, Job.tenant_id == current_tenant.id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    scraper = GitHubScraper()
    profile = await scraper.extract_profile(body.github_url)
    if not profile:
        raise HTTPException(status_code=400, detail="Could not extract GitHub profile")

    resume_data = ResumeSchema(
        contact=profile["contact"],
        summary=profile["summary"],
        skills=profile["skills"],
        projects=profile["projects"]
    )
    
    jd_schema = JobDescriptionSchema(**job.parsed_json)
    match_result = engine.calculate_match(jd_schema, resume_data)
    explanation = MatchExplainer.explain(match_result, jd_schema, resume_data)
    
    db_cand = Candidate(
        job_id=body.job_id,
        name=profile["contact"]["name"] or "GitHub User",
        email=profile["contact"]["email"] or "unknown@github.com",
        overall_score=match_result["overall_score"],
        breakdown=match_result["breakdown"],
        explanation=explanation,
        parsed_resume_json=resume_data.model_dump()
    )
    db.add(db_cand)
    await db.commit()
    await db.refresh(db_cand)
    
    return {"status": "success", "candidate_id": db_cand.id, "score": db_cand.overall_score}

@router.get("/jobs/{job_id}/candidates/", response_model=List[CandidateResponse])
async def list_candidates(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
    status: Optional[str] = Query(None, description="Filter by status: new, shortlisted, hired, rejected"),
    search: Optional[str] = Query(None, description="Search by candidate name or email"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum match score (0.0–1.0)"),
    sort_by: Optional[str] = Query("score", description="Sort by: score, name, date"),
    limit: int = Query(100, ge=1, le=500, description="Number of results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    r = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")

    query = select(Candidate).where(Candidate.job_id == job_id)

    # Apply filters
    if status and status in VALID_STATUSES:
        query = query.where(Candidate.status == status)
    if min_score is not None:
        query = query.where(Candidate.overall_score >= min_score)
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(Candidate.name.ilike(search_term), Candidate.email.ilike(search_term))
        )

    # Apply sorting
    if sort_by == "name":
        query = query.order_by(Candidate.name.asc())
    elif sort_by == "date":
        query = query.order_by(Candidate.created_at.desc())
    else:  # default: score
        query = query.order_by(Candidate.overall_score.desc())

    # Pagination
    query = query.limit(limit).offset(offset)

    res = await db.execute(query)
    return res.scalars().all()

@router.patch("/candidates/{candidate_id}/status", response_model=CandidateResponse)
async def update_candidate_status(
    candidate_id: int,
    body: CandidateStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")

    res = await db.execute(
        select(Candidate).join(Job).where(
            Candidate.id == candidate_id,
            Job.tenant_id == current_tenant.id
        )
    )
    candidate = res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if candidate.status != body.status:
        history = CandidateStatusHistory(
            candidate_id=candidate.id,
            old_status=candidate.status or "new",
            new_status=body.status
        )
        db.add(history)
        candidate.status = body.status
        await db.commit()
        await db.refresh(candidate)
        
    return candidate

# ─────────────────────────────────────────
#  Bulk Actions
# ─────────────────────────────────────────

class BulkStatusUpdate(BaseModel):
    candidate_ids: List[int]
    status: str

class BulkDelete(BaseModel):
    candidate_ids: List[int]

@router.post("/candidates/bulk-status")
async def bulk_update_status(
    body: BulkStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Update status for multiple candidates at once."""
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    if not body.candidate_ids:
        raise HTTPException(status_code=400, detail="No candidate IDs provided")

    res = await db.execute(
        select(Candidate).join(Job).where(
            Candidate.id.in_(body.candidate_ids),
            Job.tenant_id == current_tenant.id
        )
    )
    candidates = res.scalars().all()
    updated_ids = []
    for candidate in candidates:
        if candidate.status != body.status:
            db.add(CandidateStatusHistory(
                candidate_id=candidate.id,
                old_status=candidate.status or "new",
                new_status=body.status
            ))
            candidate.status = body.status
            updated_ids.append(candidate.id)
    await db.commit()
    return {"updated": len(updated_ids), "ids": updated_ids}

@router.post("/candidates/bulk-delete")
async def bulk_delete_candidates(
    body: BulkDelete,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    """Delete multiple candidates at once."""
    if not body.candidate_ids:
        raise HTTPException(status_code=400, detail="No candidate IDs provided")
    res = await db.execute(
        select(Candidate).join(Job).where(
            Candidate.id.in_(body.candidate_ids),
            Job.tenant_id == current_tenant.id
        )
    )
    candidates = res.scalars().all()
    deleted_count = len(candidates)
    for candidate in candidates:
        await db.delete(candidate)
    await db.commit()
    return {"deleted": deleted_count}

@router.patch("/candidates/{candidate_id}/notes", response_model=CandidateResponse)
async def update_candidate_notes(
    candidate_id: int,
    body: CandidateNotesUpdate,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    res = await db.execute(
        select(Candidate).join(Job).where(
            Candidate.id == candidate_id,
            Job.tenant_id == current_tenant.id
        )
    )
    candidate = res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.notes = body.notes
    await db.commit()
    await db.refresh(candidate)
    return candidate

@router.delete("/candidates/{candidate_id}", status_code=204)
async def delete_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    res = await db.execute(
        select(Candidate).join(Job).where(
            Candidate.id == candidate_id,
            Job.tenant_id == current_tenant.id
        )
    )
    candidate = res.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    await db.delete(candidate)
    await db.commit()

@router.get("/jobs/{job_id}/candidates/export")
async def export_candidates_csv(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    r = await db.execute(
        select(Job).where(Job.id == job_id, Job.tenant_id == current_tenant.id)
    )
    job = r.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    res = await db.execute(
        select(Candidate)
        .where(Candidate.job_id == job_id)
        .order_by(Candidate.overall_score.desc())
    )
    candidates = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Rank", "Name", "Email", "Overall Score (%)",
        "Semantic Similarity (%)", "Skill Match (%)",
        "Experience Fit (%)", "Education Fit (%)", "Status", "Notes"
    ])
    for i, c in enumerate(candidates):
        bd = c.breakdown or {}
        writer.writerow([
            i + 1, c.name, c.email,
            f"{c.overall_score * 100:.1f}",
            f"{bd.get('semantic_similarity', 0) * 100:.1f}",
            f"{bd.get('skill_overlap', 0) * 100:.1f}",
            f"{bd.get('experience_fit', 0) * 100:.1f}",
            f"{bd.get('education_fit', 0) * 100:.1f}",
            c.status or "new",
            (c.notes or "").replace("\n", " ")
        ])

    output.seek(0)
    safe_title = job.title.replace(" ", "_").replace("/", "-")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={safe_title}_candidates.csv"}
    )

# ─────────────────────────────────────────
#  Analytics
# ─────────────────────────────────────────

@router.get("/analytics/", response_model=AnalyticsResponse)
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant)
):
    # All jobs for tenant
    jobs_res = await db.execute(
        select(Job).where(Job.tenant_id == current_tenant.id)
    )
    jobs = jobs_res.scalars().all()
    job_ids = [j.id for j in jobs]

    if not job_ids:
        return AnalyticsResponse(
            total_jobs=0, total_candidates=0, avg_score=0.0,
            shortlisted_count=0, hired_count=0, rejected_count=0,
            top_candidates=[], score_distribution=[], skills_gap=[],
            time_to_hire_days=0.0, pass_through_rate=0.0
        )

    # All candidates
    cands_res = await db.execute(
        select(Candidate).where(Candidate.job_id.in_(job_ids))
    )
    all_candidates = cands_res.scalars().all()

    total_candidates = len(all_candidates)
    avg_score = sum(c.overall_score for c in all_candidates) / total_candidates if total_candidates else 0
    shortlisted = sum(1 for c in all_candidates if c.status == "shortlisted")
    hired = sum(1 for c in all_candidates if c.status == "hired")
    rejected = sum(1 for c in all_candidates if c.status == "rejected")

    # Top 5 candidates overall
    sorted_cands = sorted(all_candidates, key=lambda c: c.overall_score, reverse=True)
    job_title_map = {j.id: j.title for j in jobs}
    top_candidates = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "overall_score": c.overall_score,
            "status": c.status or "new",
            "job_title": job_title_map.get(c.job_id, f"Job #{c.job_id}")
        }
        for c in sorted_cands[:5]
    ]

    # Score distribution (buckets of 10)
    buckets = {f"{i*10}-{(i+1)*10}%": 0 for i in range(10)}
    for c in all_candidates:
        pct = int(c.overall_score * 100)
        bucket_key = f"{(pct // 10) * 10}-{(pct // 10 + 1) * 10}%"
        if bucket_key in buckets:
            buckets[bucket_key] += 1
    score_distribution = [{"range": k, "count": v} for k, v in buckets.items()]

    # Skills gap: collect all JD required skills vs candidate skills
    from collections import Counter
    missing_skills_counter = Counter()
    for job in jobs:
        jd_skills = set(s.lower() for s in (
            job.parsed_json.get("skills") or job.parsed_json.get("required_skills") or []
        ))
        job_cands = [c for c in all_candidates if c.job_id == job.id]
        for c in job_cands:
            cand_skills = set(s.lower() for s in (
                (c.parsed_resume_json or {}).get("skills") or []
            ))
            for skill in jd_skills:
                if skill not in cand_skills:
                    missing_skills_counter[skill] += 1

    skills_gap = [
        {"skill": skill, "missing_count": count}
        for skill, count in missing_skills_counter.most_common(10)
    ]

    # Advanced Metrics Calculation
    # 1. Pass-Through Rate: % of candidates that moved from 'new' to 'shortlisted' or 'hired'
    moved_forward = shortlisted + hired
    pass_through_rate = (moved_forward / total_candidates * 100) if total_candidates > 0 else 0.0

    # 2. Time-to-Hire: average days between Candidate.created_at and CandidateStatusHistory (new_status='hired')
    hist_res = await db.execute(
        select(CandidateStatusHistory).where(CandidateStatusHistory.candidate_id.in_([c.id for c in all_candidates]))
    )
    histories = hist_res.scalars().all()
    
    hire_times = []
    for h in histories:
        if h.new_status == "hired":
            cand = next((c for c in all_candidates if c.id == h.candidate_id), None)
            if cand and cand.created_at:
                delta = h.changed_at - cand.created_at
                hire_times.append(delta.total_seconds() / 86400.0)
    
    time_to_hire_days = sum(hire_times) / len(hire_times) if hire_times else 0.0

    return AnalyticsResponse(
        total_jobs=len(jobs),
        total_candidates=total_candidates,
        avg_score=round(avg_score, 4),
        shortlisted_count=shortlisted,
        hired_count=hired,
        rejected_count=rejected,
        top_candidates=top_candidates,
        score_distribution=score_distribution,
        skills_gap=skills_gap,
        time_to_hire_days=round(time_to_hire_days, 1),
        pass_through_rate=round(pass_through_rate, 1)
    )
