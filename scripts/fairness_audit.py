import os
import random
import numpy as np
from scipy.stats import pearsonr
from src.matching.engine import MatchingEngine
from src.matching.jd_parser import JDParser
from src.schema import ResumeSchema, Experience, Education, ContactInfo

# Reproducibility
random.seed(42)

# Config
NUM_CANDIDATES = 100
TOP_K_PERCENT = 0.30

# Proxy variables
TIERS = {"Ivy": 1, "State": 0}
NAMES_MALE = ["John Smith", "Michael Chang", "Jamal Washington", "David Cohen"]
NAMES_FEMALE = ["Mary Johnson", "Wei Chen", "Latoya Williams", "Sarah Levy"]
GENDERS = {"Male": 1, "Female": 0}

def generate_candidates():
    candidates = []
    for i in range(NUM_CANDIDATES):
        tier = random.choice(["Ivy", "State"])
        grad_year = random.randint(1990, 2022) # Proxy for age
        
        gender = random.choice(["Male", "Female"])
        name = random.choice(NAMES_MALE if gender == "Male" else NAMES_FEMALE)
        
        # Keep qualifications constant
        skills = ["Python", "AWS", "SQL", "Docker"]
        
        # Everyone has 5 years of experience to normalize experience score
        exp = Experience(company="Tech Corp", role="Software Engineer", 
                         start_date="2018-01-01", end_date="2023-01-01")
                         
        edu = Education(institution=tier, degree="Bachelor's in CS", end_date=str(grad_year))
        
        resume = ResumeSchema(
            contact=ContactInfo(name=name),
            skills=skills,
            experience=[exp],
            education=[edu],
            summary=f"Experienced engineer. Graduated from {tier} in {grad_year}."
        )
        
        candidates.append({
            "resume": resume,
            "meta": {
                "tier": TIERS[tier],
                "grad_year": grad_year,
                "gender": GENDERS[gender] # Simple binary for testing disparate impact
            }
        })
    return candidates

def calculate_adverse_impact(scores, metadata, feature, high_val, low_val):
    # Sort candidates by score descending
    ranked = sorted(zip(scores, metadata), key=lambda x: x[0], reverse=True)
    top_k = int(len(ranked) * TOP_K_PERCENT)
    selected = ranked[:top_k]
    
    # Calculate selection rates
    high_group_total = sum(1 for _, m in ranked if m[feature] == high_val)
    low_group_total = sum(1 for _, m in ranked if m[feature] == low_val)
    
    if high_group_total == 0 or low_group_total == 0:
        return 1.0
        
    high_selected = sum(1 for _, m in selected if m[feature] == high_val)
    low_selected = sum(1 for _, m in selected if m[feature] == low_val)
    
    sr_high = high_selected / high_group_total
    sr_low = low_selected / low_group_total
    
    if sr_high == 0:
        return 1.0
        
    return sr_low / sr_high

def run_audit(candidates, jd_text, redact=False):
    engine = MatchingEngine()
    parser = JDParser()
    jd = parser.parse(jd_text)
    
    scores = []
    metadata = []
    
    for c in candidates:
        resume = c["resume"].model_copy(deep=True)
        if redact:
            # Mitigation: remove proxy clues from text
            resume.summary = "Experienced engineer."
            for edu in resume.education:
                edu.institution = "University"
                edu.end_date = None
                
        match = engine.calculate_match(jd, resume)
        scores.append(match["overall_score"])
        metadata.append(c["meta"])
        
    # Calculate Correlations
    correlations = {}
    for feature in ["tier", "grad_year", "gender"]:
        feats = [m[feature] for m in metadata]
        # if scores are completely flat, pearsonr throws a warning and returns nan
        if len(set(scores)) > 1:
            r, _ = pearsonr(feats, scores)
            correlations[feature] = r
        else:
            correlations[feature] = 0.0
            
    # Calculate Adverse Impact (Four-Fifths rule)
    ai_ratios = {}
    ai_ratios["tier"] = calculate_adverse_impact(scores, metadata, "tier", high_val=1, low_val=0)
    ai_ratios["gender"] = calculate_adverse_impact(scores, metadata, "gender", high_val=1, low_val=0)
    
    # For grad_year, split by median
    median_year = np.median([m["grad_year"] for m in metadata])
    # Let's say "high" is recent grads (age proxy)
    for m in metadata:
        m["recent_grad"] = 1 if m["grad_year"] > median_year else 0
    ai_ratios["age"] = calculate_adverse_impact(scores, metadata, "recent_grad", high_val=1, low_val=0)
    
    return correlations, ai_ratios

def generate_report():
    jd_text = "Looking for a Software Engineer with 3 years of experience. Must know Python, AWS, SQL, and Docker. Bachelor's degree required."
    candidates = generate_candidates()
    
    print("Running baseline audit...")
    corr_base, ai_base = run_audit(candidates, jd_text, redact=False)
    
    print("Running mitigation audit...")
    corr_mit, ai_mit = run_audit(candidates, jd_text, redact=True)
    
    with open("MODEL_CARD.md", "w") as f:
        f.write("# Model Card: Matching Engine\n\n")
        f.write("## Fairness Audit Findings\n\n")
        f.write("We audited the composite matching engine against a synthetic dataset of 100 candidates. All candidates possessed identical objective qualifications (skills, 5 years experience, Bachelor's degree). We varied University Tier, Graduation Year (age proxy), and Name (gender proxy).\n\n")
        
        f.write("### Baseline Run\n")
        f.write("Pearson Correlations (closer to 0 is better):\n")
        for k, v in corr_base.items(): f.write(f"- {k}: {v:.3f}\n")
        f.write("\nAdverse Impact Ratios (Top 30% Selection Rate, < 0.8 is flagged):\n")
        for k, v in ai_base.items(): 
            flag = " 🚩 FLAGGED" if v < 0.8 else ""
            f.write(f"- {k}: {v:.3f}{flag}\n")
            
        f.write("\n### Mitigation Run (Redacted Text)\n")
        f.write("We reran the engine while redacting university names and graduation dates from the resume text before generating embeddings.\n\n")
        f.write("Pearson Correlations:\n")
        for k, v in corr_mit.items(): f.write(f"- {k}: {v:.3f}\n")
        f.write("\nAdverse Impact Ratios:\n")
        for k, v in ai_mit.items(): 
            flag = " 🚩 FLAGGED" if v < 0.8 else ""
            f.write(f"- {k}: {v:.3f}{flag}\n")
            
if __name__ == "__main__":
    generate_report()
