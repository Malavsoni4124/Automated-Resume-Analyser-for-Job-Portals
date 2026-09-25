from typing import Dict, Any
from ..schema import JobDescriptionSchema, ResumeSchema

class MatchExplainer:
    @staticmethod
    def explain(match_results: Dict[str, Any], jd: JobDescriptionSchema, resume: ResumeSchema) -> str:
        """Generates a structured, detailed human-readable explanation of the match score."""
        bd = match_results["breakdown"]
        score = match_results["overall_score"] * 100
        years = match_results.get("years_of_experience", 0)
        
        lines = [f"Overall Match Score: {score:.0f}%\n"]
        
        # — Semantic Similarity —
        sem = bd["semantic_similarity"] * 100
        if sem >= 75:
            lines.append(f"✦ Strong semantic alignment ({sem:.0f}%): The candidate's background closely mirrors the language and domain of this role.")
        elif sem >= 50:
            lines.append(f"✦ Moderate semantic alignment ({sem:.0f}%): The candidate's background partially overlaps with the role's domain.")
        else:
            lines.append(f"✦ Weak semantic alignment ({sem:.0f}%): The candidate's background shows limited overlap with the role's requirements.")

        # — Skills —
        if jd.skills:
            res_skills = getattr(resume, 'skills', []) or []
            res_skills_set = set(s.lower() for s in res_skills)
            missing = [s for s in jd.skills if s.lower() not in res_skills_set]
            matched = [s for s in jd.skills if s.lower() in res_skills_set]
            skill_pct = bd["skill_overlap"] * 100

            if not missing:
                lines.append(f"✦ Skills: Full match — all {len(jd.skills)} required skills are present ({', '.join(matched[:5])}).")
            else:
                lines.append(
                    f"✦ Skills: {skill_pct:.0f}% match ({len(matched)}/{len(jd.skills)} required skills). "
                    f"Present: {', '.join(matched[:4])}. "
                    f"Missing: {', '.join(missing[:4])}{'...' if len(missing) > 4 else ''}."
                )
        
        # — Experience —
        req_years = jd.min_years_experience
        if req_years > 0:
            exp_pct = bd["experience_fit"] * 100
            if years >= req_years:
                lines.append(f"✦ Experience: {years:.1f} yrs detected — meets the {req_years}-year requirement. ({exp_pct:.0f}% fit)")
            else:
                lines.append(f"✦ Experience: {years:.1f} yrs detected — below the {req_years}-year requirement. ({exp_pct:.0f}% fit)")
        else:
            lines.append(f"✦ Experience: {years:.1f} yrs detected — no minimum requirement specified.")

        # — Education —
        if jd.required_degree:
            edu_fit = bd["education_fit"]
            if edu_fit >= 1.0:
                lines.append(f"✦ Education: Meets or exceeds the {jd.required_degree} requirement.")
            elif edu_fit >= 0.5:
                lines.append(f"✦ Education: One tier below the {jd.required_degree} requirement (partial credit applied).")
            else:
                lines.append(f"✦ Education: Does not meet the {jd.required_degree} requirement.")
        else:
            lines.append("✦ Education: No degree requirement specified for this role.")

        return "\n".join(lines)
