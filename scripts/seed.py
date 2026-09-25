import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import Tenant, Job, User, Candidate
from src.database.session import async_session

async def seed():
    async with async_session() as session:
        # Get the first tenant
        result = await session.execute(select(Tenant).limit(1))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            print("No tenant found. Run migrate.py first.")
            return

        # Check if jobs already exist
        result = await session.execute(select(Job).where(Job.tenant_id == tenant.id))
        if result.scalars().first():
            print("Jobs already exist. Skipping seed.")
            return

        print("Seeding sample jobs and candidates...")
        job_titles = [
            "Senior React Developer", "Backend Python Engineer", "Product Manager", 
            "Data Scientist", "DevOps Engineer", "UI/UX Designer", 
            "Full Stack Developer", "Machine Learning Engineer", "QA Tester", 
            "Mobile App Developer", "Cloud Architect", "Technical Writer", 
            "Scrum Master", "Cybersecurity Analyst", "Systems Administrator"
        ]
        job_skills = [
            ["React", "JavaScript", "TypeScript"], ["Python", "Django", "FastAPI"], ["Agile", "Jira", "Roadmaps"],
            ["Python", "Pandas", "Scikit-Learn"], ["AWS", "Docker", "Kubernetes"], ["Figma", "Sketch", "Prototyping"],
            ["React", "Node.js", "MongoDB"], ["PyTorch", "TensorFlow", "Python"], ["Selenium", "Cypress", "QA"],
            ["Swift", "Kotlin", "React Native"], ["AWS", "Azure", "GCP"], ["Documentation", "Confluence", "API"],
            ["Agile", "Scrum", "Kanban"], ["Security", "Network", "Penetration Testing"], ["Linux", "Windows", "Networking"]
        ]
        
        jobs = []
        for i in range(15):
            job = Job(
                tenant_id=tenant.id,
                title=job_titles[i],
                raw_text=f"We are looking for a {job_titles[i]}.",
                parsed_json={"title": job_titles[i], "skills": job_skills[i], "experience_years": 3 + (i%5)}
            )
            jobs.append(job)
        
        session.add_all(jobs)
        await session.commit()
        
        for job in jobs:
            await session.refresh(job)
        
        import random
        candidates = []
        for i in range(1, 51):
            job = random.choice(jobs)
            status = random.choice(['new', 'shortlisted', 'rejected', 'hired'])
            score = random.uniform(0.3, 0.95)
            c = Candidate(
                job_id=job.id,
                name=f"Candidate {i}",
                email=f"candidate{i}@example.com",
                overall_score=score,
                status=status,
                parsed_resume_json={"name": f"Candidate {i}", "skills": ["Python"]},
                breakdown={"skills": score, "experience": score},
                explanation="Good fit."
            )
            candidates.append(c)
        session.add_all(candidates)
        await session.commit()
        
        print(f"Successfully seeded {len(jobs)} jobs and {len(candidates)} candidates!")

if __name__ == "__main__":
    asyncio.run(seed())
