# Model Card: Matching Engine

## Fairness Audit Findings

We audited the composite matching engine against a synthetic dataset of 100 candidates. All candidates possessed identical objective qualifications (skills, 5 years experience, Bachelor's degree). We varied University Tier, Graduation Year (age proxy), and Name (gender proxy).

### Baseline Run
Pearson Correlations (closer to 0 is better):
- tier: -0.890
- grad_year: 0.165
- gender: 0.093

Adverse Impact Ratios (Top 30% Selection Rate, < 0.8 is flagged):
- tier: 1.000
- gender: 0.875
- age: 2.343

### Mitigation Run (Redacted Text)
We reran the engine while redacting university names and graduation dates from the resume text before generating embeddings.

Pearson Correlations:
- tier: 0.000
- grad_year: 0.000
- gender: 0.000

Adverse Impact Ratios:
- tier: 1.098
- gender: 0.875
- age: 1.114
