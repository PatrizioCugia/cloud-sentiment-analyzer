# Nordic AI Lead Generation System

Automated lead generation system for discovering and enriching Nordic AI companies using LinkedIn, Apollo.io, and AI-powered analysis.

## Features

- LinkedIn discovery via Apify actor
- Apollo.io enrichment for firmographics and technologies
- Contact finding for key decision-makers
- AI-based classification and strategy generation (Gemini)
- Progressive save to Apify dataset and summary to KV store

## Input

```json
{
  "searchQuery": "artificial intelligence machine learning",
  "locations": ["Denmark", "Sweden", "Norway", "Finland"],
  "maxCompanies": 20,
  "numTargets": 5,
  "apolloApiKey": "your_key_here",
  "geminiApiKey": "your_key_here",
  "maxContactsPerCompany": 3,
  "enableApolloEnrichment": true,
  "enableContactFinding": true
}
```

## Output

Each dataset item includes:
- company (basic + enriched)
- contacts
- technology indicators
- generated outreach strategy
- generated_at timestamp

## Notes

- Use Apify residential proxies for reliability
- Respect Apollo rate limits (add delays)
- Works without Apollo if enrichment/contact finding disabled