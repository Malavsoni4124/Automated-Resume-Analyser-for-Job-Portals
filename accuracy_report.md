# Phase 1 Extraction Accuracy Report

**Total Resumes Evaluated**: 35

## 1. Per-Category Breakdown

### Category: STANDARD
- **Email**: 27 / 27 (100.0%)
- **Phone**: 1 / 1 (100.0%)
- **Name**: 1 / 27 (3.7%)
- **Company**: 0 / 1 (0.0%)
- **Role**: 0 / 1 (0.0%)
- **Degree**: 0 / 1 (0.0%)
- **Skills (Recall)**: 55 / 56 (98.2%)

### Category: VALIDATION
- **Email**: 5 / 5 (100.0%)
- **Phone**: 1 / 1 (100.0%)
- **Name**: 1 / 5 (20.0%)
- **Company**: 0 / 6 (0.0%)
- **Role**: 0 / 6 (0.0%)
- **Degree**: 0 / 5 (0.0%)
- **Skills (Recall)**: 4 / 5 (80.0%)

### Category: SKILLS_ONLY
- **Email**: 1 / 1 (100.0%)
- **Phone**: 0 / 0 (0.0%)
- **Name**: 1 / 1 (100.0%)
- **Company**: 0 / 0 (0.0%)
- **Role**: 0 / 0 (0.0%)
- **Degree**: 0 / 0 (0.0%)
- **Skills (Recall)**: 4 / 4 (100.0%)

### Category: UNSTRUCTURED
- **Email**: 1 / 1 (100.0%)
- **Phone**: 0 / 0 (0.0%)
- **Name**: 1 / 1 (100.0%)
- **Company**: 0 / 1 (0.0%)
- **Role**: 0 / 0 (0.0%)
- **Degree**: 0 / 0 (0.0%)
- **Skills (Recall)**: 2 / 2 (100.0%)

## 2. LLM Fallback & Disagreement Telemetry

**Confidence Threshold Used for Contact Section**: 0.5
*Justification: If spaCy fails to find a PERSON entity (confidence 0.0), it falls back to LLM. A 0.5 threshold ensures we aggressively fallback if extraction is incomplete, guaranteeing high recall on critical contact fields.*

**LLM Fallbacks Triggered**: 29
**spaCy vs LLM Disagreements Logged**: 0


*Note: Ran with a Fake LLM to forcefully exercise disagreement and fallback code paths.*