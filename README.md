# LeadGenius Pro Agent API Skill

This skill provides a set of tools and scripts for AI agents to interact with the LeadGenius Pro Agent API.

## Features

- **Lead Management**: Create, list, and update leads.
- **Campaign Operations**: Launch and track ABM campaigns.
- **Authentication**: Supports Bearer tokens.
- **Environment Support**: Automatically loads `LEADGENIUS_API_KEY` or `LGP_API_KEY` from a `.env` file in the project root.
- **Statistics**: Includes a script to aggregate leads per client.

## Installation

This skill can be used directly by AI agents. To use the scripts manually:

```bash
pip install requests
```

## Available Scripts

- `scripts/api_call.py`: A versatile CLI for making arbitary API calls.
- `scripts/rest_lead_stats.py`: Summarizes lead counts per `client_id` using the REST API.
- `scripts/lead_distribution.py`: Advanced distribution audit using GraphQL (requires AppSync key).

## Development

Changes in version 1.0.1:
- Fixed authentication header to use `Bearer` scheme.
- Added support for `LEADGENIUS_API_KEY` environment variable.
- Added `rest_lead_stats.py` for quick visibility into lead distribution.
