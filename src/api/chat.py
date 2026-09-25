from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import google.generativeai as genai
import json

from src.database.session import get_db
from src.database.models import Job, Candidate
from src.config import settings

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    job_id: int

class ChatResponse(BaseModel):
    reply: str
    candidate_ids: list[int] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Takes a natural language query from the recruiter and filters candidates.
    """
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key missing")
        
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 1. Fetch all candidates for the context
    result = await db.execute(select(Candidate).where(Candidate.job_id == request.job_id))
    candidates = result.scalars().all()
    
    if not candidates:
        return ChatResponse(reply="There are no candidates in this job pipeline yet.", candidate_ids=[])
        
    # 2. Build context
    context = "Here are the candidates in the pipeline for this job:\n"
    for c in candidates:
        context += f"Candidate ID: {c.id}\nScore: {c.overall_score}\n"
        context += f"Skills: {json.dumps(c.breakdown.get('skills', {}).get('matched_skills', [])) if c.breakdown else 'N/A'}\n"
        context += f"Experience: {c.breakdown.get('experience', {}).get('candidate_years', 0) if c.breakdown else 0} years\n"
        context += "---\n"
        
    prompt = (
        "You are an expert AI Recruiter Copilot. The user (a recruiter) is asking a question about the candidates in their pipeline. "
        "Based on the provided candidate data, answer their question naturally.\n\n"
        "ALSO: If the user's request implies filtering or selecting specific candidates, "
        "you MUST include a JSON array at the very end of your response (on a new line) containing the Candidate IDs that match. "
        "Example: [1, 4, 5]\n\n"
        f"Data Context:\n{context}\n\n"
        f"Recruiter Question: {request.message}"
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Try to extract the JSON array of IDs from the end of the text
        candidate_ids = []
        reply = text
        import re
        match = re.search(r'\[([\d,\s]+)\]$', text.strip())
        if match:
            try:
                candidate_ids = [int(i.strip()) for i in match.group(1).split(',') if i.strip()]
                # Remove the array from the reply
                reply = text[:match.start()].strip()
            except ValueError:
                pass
                
        return ChatResponse(reply=reply, candidate_ids=candidate_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot error: {e}")
