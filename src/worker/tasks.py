import os
import asyncio
from typing import Dict, Any
from .celery_app import celery_app
from sqlalchemy.future import select

from src.database.session import async_session
from src.database.models import Job, Candidate
from src.api.dependencies import get_resume_parser, get_matching_engine
from src.schema import JobDescriptionSchema
from src.matching.explainer import MatchExplainer

parser = get_resume_parser()
engine = get_matching_engine()

async def async_process_resume(job_id: int, file_path: str):
    async with async_session() as db:
        # Check job
        result = await db.execute(select(Job).where(Job.id == job_id))
        db_job = result.scalar_one_or_none()
        if not db_job:
            return {"status": "error", "message": "Job not found"}
            
        parse_result = parser.parse(file_path)
        if parse_result.status != "success" or not parse_result.data:
            return {"status": "error", "message": "Failed to parse resume"}
            
        resume_data = parse_result.data
        jd_schema = JobDescriptionSchema(**db_job.parsed_json)
        match_result = engine.calculate_match(jd_schema, resume_data)
        explanation = MatchExplainer.explain(match_result, jd_schema, resume_data)
        
        name = resume_data.contact.name if resume_data.contact else "Unknown"
        email = resume_data.contact.email if resume_data.contact else "Unknown"
        
        db_cand = Candidate(
            job_id=job_id,
            name=name,
            email=email,
            overall_score=match_result["overall_score"],
            breakdown=match_result["breakdown"],
            explanation=explanation,
            parsed_resume_json=resume_data.model_dump()
        )
        db.add(db_cand)
        await db.commit()
        await db.refresh(db_cand)
        
        return {"status": "success", "candidate_id": db_cand.id, "score": db_cand.overall_score}

@celery_app.task(name="process_resume_task")
def process_resume_task(job_id: int, file_path: str) -> Dict[str, Any]:
    try:
        # Run the async function inside a sync Celery worker
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    result = loop.run_until_complete(async_process_resume(job_id, file_path))
    
    # Clean up the temp file
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return result
