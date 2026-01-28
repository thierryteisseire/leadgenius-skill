# LeadGenius Pro Agent API Skill

A specialized skill for AI agents to interact with the LeadGenius Pro B2B platform. This skill enables agents to manage ABM campaigns, enrich leads, and automate outreach workflows.

## 🚀 Installation

Add this skill to your agent environment:

```bash
npx skills add https://github.com/epsimo-agent/leadgenius-skill
```

## 🛠️ Features

- **Lead Lifecycle**: List, create, and transition lead statuses.
- **AI Enrichment**: Trigger automated data augmentation for person and company data.
- **Campaign Management**: Handle ABM targets and monitor ROI metrics.
- **Analytics**: Pull pipeline performance and conversion trends.
- **Integrations**: Sync data with CRMs and configure webhooks.

## 📂 Repository Structure

- `SKILL.md`: Core instructions for AI agents.
- `references/`: Detailed documentation.
  - `api_reference.md`: Human-readable endpoint documentation.
  - `openapi.json`: Machine-readable specification.
- `scripts/`: Helper utilities.
  - `api_call.py`: CLI tool for testing API requests.

## 🔑 Requirements

To use this skill, you need a LeadGenius Pro API Key.
- Base URL: `/api/agent`
- Headers: `X-API-Key: lgp_your_key`

## ⚖️ License
MIT License. See [LICENSE.txt](LICENSE.txt) for details.
