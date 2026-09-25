import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from src.database.models import Base, Tenant, Job, Candidate
from src.matching.jd_parser import JDParser
from src.api.auth import get_password_hash

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ats.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

jd_parser = JDParser()

JOBS = [
    {
        "title": "Senior Python & AI Engineer",
        "raw_text": """We are looking for a Senior Python & AI Engineer with 4+ years of experience.
Requirements:
- Proficiency in Python, FastAPI, PyTorch, Docker, PostgreSQL, React
- Experience with machine learning pipelines and REST APIs
- Strong understanding of software design patterns
- Bachelor's degree in Computer Science or related field
- Experience with cloud platforms (AWS/GCP) is a plus
Responsibilities:
- Design and implement scalable AI-powered microservices
- Collaborate with cross-functional teams on ML model deployment
- Optimize performance and reliability of production systems"""
    },
    {
        "title": "Frontend React Developer",
        "raw_text": """Seeking an experienced Frontend Developer to build world-class user interfaces.
Requirements:
- 3+ years of experience with React, TypeScript, JavaScript
- Proficiency in CSS, HTML, Webpack, Vite, Next.js
- Experience with REST APIs, GraphQL, state management (Redux, Zustand)
- Knowledge of performance optimization and accessibility (WCAG)
- Bachelor's degree preferred
Responsibilities:
- Build responsive, pixel-perfect UIs from Figma designs
- Write clean, testable component code
- Collaborate with designers and backend engineers"""
    },
    {
        "title": "Data Scientist",
        "raw_text": """We need a Data Scientist to drive insights from large datasets.
Requirements:
- Master's degree in Statistics, Mathematics, or Computer Science
- 2+ years of hands-on experience with Python, Pandas, NumPy, Scikit-learn
- Strong knowledge of machine learning algorithms, A/B testing, SQL
- Experience with Tableau, Power BI, or similar BI tools
- Familiarity with TensorFlow or PyTorch is a plus
Responsibilities:
- Build and deploy predictive models
- Conduct exploratory data analysis and communicate findings
- Partner with product teams to define metrics"""
    },
    {
        "title": "DevOps / Cloud Engineer",
        "raw_text": """We are hiring a DevOps Engineer to scale our infrastructure.
Requirements:
- 3+ years of experience with AWS, GCP, or Azure
- Strong knowledge of Kubernetes, Docker, Terraform, Ansible
- Proficiency with CI/CD pipelines: GitHub Actions, Jenkins, ArgoCD
- Experience with monitoring tools: Prometheus, Grafana, Datadog
- Scripting in Bash, Python
- Bachelor's degree in Computer Science or equivalent
Responsibilities:
- Design and maintain cloud infrastructure
- Automate deployment pipelines
- Ensure 99.9% uptime SLAs"""
    },
    {
        "title": "ML Research Scientist",
        "raw_text": """Looking for an ML Research Scientist to push the boundaries of AI.
Requirements:
- PhD in Machine Learning, Computer Science, or related field
- 2+ years of research experience with publications in NeurIPS, ICML, ICLR preferred
- Deep expertise in PyTorch, JAX, transformers, LLMs, RLHF
- Strong mathematical foundations: linear algebra, probability, optimization
- Experience with distributed training on GPU clusters
Responsibilities:
- Conduct original ML research
- Design and run experiments at scale
- Collaborate with engineering to productionize models"""
    },
    {
        "title": "Full Stack Developer",
        "raw_text": """We want a versatile Full Stack Developer who can own features end-to-end.
Requirements:
- 3+ years experience with Node.js, Express, React or Vue.js
- Knowledge of MongoDB, PostgreSQL, Redis
- Familiarity with Docker, Linux, REST APIs, GraphQL
- Experience with testing frameworks (Jest, Pytest, Cypress)
- Bachelor's degree in Computer Science or equivalent
Responsibilities:
- Build and maintain full-stack web applications
- Write backend APIs and frontend components
- Participate in code reviews and architecture discussions"""
    },
    {
        "title": "Product Manager — AI Products",
        "raw_text": """Seeking a Product Manager to lead our AI-powered product line.
Requirements:
- 5+ years of product management experience in B2B SaaS
- Familiarity with machine learning concepts and AI products
- Proven track record of shipping products used by 10k+ users
- Strong skills in Jira, Confluence, Figma, SQL
- Excellent communication and stakeholder management
- MBA or Bachelor's degree required
Responsibilities:
- Define product roadmap and prioritize features
- Work closely with engineering, design, and go-to-market teams
- Translate user research into product decisions"""
    },
    {
        "title": "Backend Go Engineer",
        "raw_text": """We are expanding our backend team with a Go Engineer.
Requirements:
- 3+ years of backend development experience with Go (Golang)
- Strong understanding of concurrency, goroutines, channels
- Experience with gRPC, Protocol Buffers, REST APIs
- Knowledge of PostgreSQL, Redis, message queues (Kafka, RabbitMQ)
- Experience with microservices architecture and Docker/Kubernetes
- Bachelor's degree in Computer Science or equivalent
Responsibilities:
- Build high-performance backend services in Go
- Design efficient APIs and database schemas
- Collaborate on system design and scalability"""
    },
]

SAMPLE_CANDIDATES = [
    {
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "resume_text": """Alex Johnson | alex.johnson@example.com | +1-555-0101 | San Francisco, CA

SUMMARY
Senior software engineer with 6 years of experience in Python, machine learning, and distributed systems.

EXPERIENCE
Senior ML Engineer — TechCorp Inc (2021 - Present)
- Built real-time recommendation engine serving 10M+ users using PyTorch and FastAPI
- Reduced model inference latency by 40% using ONNX and TensorRT optimization
- Led team of 4 engineers on AI pipeline redesign

Software Engineer — DataFlow Systems (2018 - 2021)
- Developed RESTful APIs with Python and Django for financial data processing
- Integrated PostgreSQL and Redis for high-throughput data pipelines
- Deployed services on AWS ECS with Docker and CI/CD via GitHub Actions

EDUCATION
B.Sc. Computer Science — Stanford University (2014 - 2018)

SKILLS
Python, FastAPI, PyTorch, TensorFlow, Docker, PostgreSQL, Redis, AWS, React, SQL, NumPy, Pandas, Git

CERTIFICATIONS
AWS Certified Solutions Architect (2022)"""
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "resume_text": """Priya Sharma | priya.sharma@example.com | Mumbai, India

SUMMARY
Data Scientist with 3 years of experience building ML models for e-commerce and fintech.

EXPERIENCE
Data Scientist — FinanceAI Pvt Ltd (2021 - Present)
- Designed credit risk model using XGBoost achieving 92% AUC
- Built real-time fraud detection pipeline with Scikit-learn and Kafka
- Created Tableau dashboards for C-suite reporting

Junior Data Analyst — RetailTech (2019 - 2021)
- Conducted A/B tests improving conversion rate by 18%
- Built SQL queries and Python scripts for ETL pipelines

EDUCATION
M.Sc. Statistics — IIT Bombay (2017 - 2019)
B.Sc. Mathematics — University of Mumbai (2014 - 2017)

SKILLS
Python, Pandas, NumPy, Scikit-learn, XGBoost, TensorFlow, SQL, Tableau, Power BI, R, Kafka"""
    },
    {
        "name": "David Chen",
        "email": "david.chen@example.com",
        "resume_text": """David Chen | david.chen@example.com | Seattle, WA

SUMMARY
Frontend-focused full stack developer with 4 years experience building SaaS products.

EXPERIENCE
Frontend Engineer — CloudSuite Inc (2022 - Present)
- Built React component library used across 5 product teams
- Migrated legacy jQuery codebase to React + TypeScript, reducing bundle size 60%
- Implemented real-time features using WebSockets and React Query

Full Stack Developer — StartupXYZ (2020 - 2022)
- Developed Node.js/Express APIs and React frontends for B2B platform
- Managed PostgreSQL schema design and database migrations
- Set up Docker + GitHub Actions CI/CD pipeline

EDUCATION
B.Sc. Computer Science — University of Washington (2016 - 2020)

SKILLS
React, TypeScript, JavaScript, Next.js, Node.js, CSS, HTML, GraphQL, PostgreSQL, Docker, Webpack, Vite, Redux"""
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if tenant 1 already exists
        result = await db.execute(select(Tenant).where(Tenant.id == 1))
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="demo", hashed_password=get_password_hash("admin123"))
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)
            print(f"Created tenant: {tenant.id}")
        else:
            print(f"Using existing tenant: {tenant.id}")

        # Check existing jobs
        existing_jobs = await db.execute(select(Job).where(Job.tenant_id == tenant.id))
        existing_titles = {j.title for j in existing_jobs.scalars().all()}

        from src.matching.engine import MatchingEngine
        from src.schema import ResumeSchema, ContactInfo, Experience, Education
        from src.matching.explainer import MatchExplainer
        import numpy as np

        engine_ml = MatchingEngine()

        for job_data in JOBS:
            if job_data["title"] in existing_titles:
                print(f"  Skipping existing job: {job_data['title']}")
                continue

            parsed_jd = jd_parser.parse(job_data["raw_text"])
            db_job = Job(
                tenant_id=tenant.id,
                title=job_data["title"],
                raw_text=job_data["raw_text"],
                parsed_json=parsed_jd.model_dump()
            )
            db.add(db_job)
            await db.commit()
            await db.refresh(db_job)
            print(f"  Created job: {db_job.id} — {db_job.title} (skills: {parsed_jd.skills[:3]}...)")

            # Seed 3 sample candidates for first 3 jobs
            if JOBS.index(job_data) < 3:
                for cand_data in SAMPLE_CANDIDATES:
                    # Build a minimal ResumeSchema from text
                    resume_schema = ResumeSchema(
                        contact=ContactInfo(name=cand_data["name"], email=cand_data["email"]),
                        summary=cand_data["resume_text"].split("EXPERIENCE")[0].split("SUMMARY")[-1].strip()[:400],
                        skills=parsed_jd.skills[:6],  # Give them matching skills for demo
                        experience=[
                            Experience(
                                company="TechCorp",
                                role="Senior Engineer",
                                start_date="2021-01",
                                end_date="Present",
                                description="Senior engineering role"
                            ),
                            Experience(
                                company="Startup",
                                role="Engineer",
                                start_date="2018-01",
                                end_date="2021-01",
                                description="Engineering role"
                            )
                        ],
                        education=[
                            Education(
                                institution="State University",
                                degree="Bachelor's",
                                major="Computer Science"
                            )
                        ]
                    )

                    match_result = engine_ml.calculate_match(parsed_jd, resume_schema)
                    explanation = MatchExplainer.explain(match_result, parsed_jd, resume_schema)

                    import random
                    # Add slight variation in scores for realism
                    base = match_result["overall_score"]
                    varied = min(1.0, max(0.0, base + random.uniform(-0.08, 0.08)))

                    cand = Candidate(
                        job_id=db_job.id,
                        name=cand_data["name"],
                        email=cand_data["email"],
                        overall_score=varied,
                        breakdown=match_result["breakdown"],
                        explanation=explanation,
                        parsed_resume_json=resume_schema.model_dump(),
                        status="new"
                    )
                    db.add(cand)
                await db.commit()
                print(f"    → Seeded {len(SAMPLE_CANDIDATES)} candidates for job {db_job.id}")

        print("\n✅ Seed complete!")
        print("   Credentials: Tenant ID=1, Password=admin123")

if __name__ == "__main__":
    asyncio.run(seed())
