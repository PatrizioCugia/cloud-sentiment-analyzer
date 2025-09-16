---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-size: 30px; }
  h1, h2, h3 { font-weight: 600; }
  .muted { color: #666; }
  table { font-size: 16px; }
---

# Cloud Providers — Sentiment Analysis

Minimal white slides • Model + Survey

---

<!-- _class: lead -->
# Model

---

## RoBERTa for Sentiment (fine‑tuned)

- Base encoder: RoBERTa (BPE tokenizer, robust contextual embeddings)
- Task: 3‑class sentiment (Positive / Negative / Neutral)
- Data: Mentions of cloud providers labeled by area (cost, performance, scalability, security, support, general)
- Fine‑tuning:
  - CLS output → dropout → linear head (3 logits)
  - Weighted cross‑entropy to handle class imbalance
  - Early stopping on macro‑F1; stratified train/val/test
- Inference: softmax; optional confidence threshold for "neutral"

Notes:
- Domain fine‑tuning > zero‑shot; captures negation and long‑range context

---

## Rules ("reinforced grammar") vs. RoBERTa

- Rules baseline:
  - Phrase lists + intensifiers/diminishers
  - Negation scope ("not good", "hardly useful")
  - Domain lexicon (cost/perf/security)
- Trade‑offs:
  - Rules → transparent, fast; brittle on paraphrase/sarcasm/context
  - RoBERTa → better generalization; needs labeled data
- Practical blend:
  - Use rules for high‑precision seeds/guardrails
  - Use RoBERTa as primary classifier; rules for QA/error analysis

---

## Results (counts by provider & area)

| Provider      | Area        | Total | Positive | Negative | Neutral |
|---------------|-------------|------:|---------:|---------:|--------:|
| AWS           | cost        | 424   | 148      | 233      | 43      |
| AWS           | general     | 477   | 201      | 219      | 57      |
| AWS           | performance | 108   | 44       | 46       | 18      |
| AWS           | scalability | 98    | 43       | 43       | 12      |
| AWS           | security    | 370   | 196      | 151      | 23      |
| AWS           | support     | 232   | 112      | 106      | 14      |
| Azure         | cost        | 85    | 33       | 37       | 15      |
| Azure         | general     | 281   | 116      | 134      | 31      |
| Azure         | performance | 21    | 6        | 12       | 3       |
| Azure         | scalability | 32    | 17       | 14       | 1       |
| Azure         | security    | 91    | 38       | 46       | 7       |
| Azure         | support     | 93    | 41       | 43       | 9       |
| Google Cloud  | cost        | 45    | 25       | 16       | 4       |
| Google Cloud  | general     | 238   | 127      | 94       | 17      |
| Google Cloud  | performance | 25    | 9        | 12       | 4       |
| Google Cloud  | scalability | 19    | 11       | 8        | 0       |
| Google Cloud  | security    | 24    | 14       | 10       | 0       |
| Google Cloud  | support     | 35    | 26       | 9        | 0       |

---

<!-- _class: lead -->
# Survey

---

## Where teams run models

- On‑premise preferred for:
  - Red tape / compliance
  - Ease of use / control
  - Security requirements
- Cloud preferred for:
  - Larger compute or larger models
  - Typical flow: prototype on‑prem → deploy/scale in cloud

---

## What matters most in the cloud

- Flexible access to raw compute power — 65%
- Transparent pricing — 65%
- Support docs — 61%
- Preference: flexible compute over prebuilt libraries
- In some roles, ease of setup/integration ≈ cost in importance

---

## Main issues

- High or unpredictable cost
- Integration difficulties
- Lack of support

Open‑ended themes:
- Integrating across environments/platforms
- Aligning local dev with cloud runtime parity
- Many use AWS/Azure to match client requests/infrastructure

---

## Conclusions

- Pricing sentiment skews negative on AWS and Azure; GCP more positive on cost/support
- Practitioners favor easy setup/integration; minimize operational complexity
- Cost and ease of integration are co‑primary drivers of provider choice

---

# Thank you