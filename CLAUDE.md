# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "Zava" -- a multi-agent AI shopping assistant built with Microsoft Azure AI Foundry. It's a workshop/lab codebase for learning to build AI apps and agents. The app is a FastAPI WebSocket chat application with a browser-based frontend (`src/chat.html`).

## Running the Application

```bash
# Activate virtual environment
cd src
source venv/Scripts/activate  # Windows (Git Bash)

# Install dependencies
pip install -r requirements.txt

# Run main chat app (default port 8000)
python chat_app.py

# Run A2A product manager app (port 8001)
cd a2a && python main.py
```

The app requires a `.env` file in `src/` -- see `src/env_sample.txt` for all required variables. Key services: Azure AI Foundry, Azure OpenAI (GPT + Phi-4), Cosmos DB, Azure Blob Storage, Application Insights.

## Architecture

### Multi-Agent System

The core is a **handoff-based multi-agent system** where a `HandoffService` (`src/services/handoff_service.py`) classifies user intent via structured outputs and routes to the appropriate agent:

- **cora** -- General shopping assistant (default). Gets conversation history + product recommendations.
- **interior_designer** -- Room design, color schemes. Gets image analysis + product data.
- **interior_designer_create_image** -- Special case: uses gpt-image-1 directly, not the agent processor.
- **cart_manager** -- Shopping cart operations. Gets full raw I/O history for state tracking.
- **customer_loyalty** -- Discount calculation. Runs once in background at session start, response delayed until first cart operation.
- **inventory_agent** -- Stock/availability checks.

All agents (except image creation) use a unified `AgentProcessor` (`src/app/agents/agent_processor.py`) that communicates with Azure AI Foundry agents via the OpenAI conversations API. Agents are referenced by name (stored as env vars like `cora`, `cart_manager`) and executed via `agent_reference` pattern.

### Key Data Flow (WebSocket)

1. User message arrives via WebSocket (`/ws`)
2. `HandoffService.classify_intent()` determines target agent domain
3. Context enrichment: image analysis (Phi-4 vision), product search (Cosmos DB via AI Search)
4. `AgentProcessor` streams response from Azure AI Foundry agent
5. Response parsed as structured JSON (`parse_agent_response`), cart/discount state updated, sent to user

### MCP (Model Context Protocol) Server

`src/app/servers/mcp_inventory_server.py` -- FastMCP server mounted at `/mcp-inventory/` on the main app. Exposes tools: `get_product_recommendations`, `check_product_inventory`, `get_customer_discount`, `generate_product_image`. Also serves agent prompts via MCP prompt resources.

`src/app/servers/mcp_inventory_client.py` -- SSE-based MCP client (`MCPShopperToolsClient`) used by `AgentProcessor` for function call execution.

### A2A (Agent-to-Agent)

`src/a2a/` -- Separate FastAPI app ("Zava Product Manager") running on port 8001 with A2A protocol support. Mounts A2A endpoints at `/a2a` with agent card discovery at `/agent-card`.

### Agent Initialization

`src/app/agents/*_initializer.py` -- Scripts to create/register agents in Azure AI Foundry using `PromptAgentDefinition`. Each agent has a corresponding prompt in `src/prompts/`.

### Tools Layer

- `src/app/tools/aiSearchTools.py` -- Product recommendations via Cosmos DB vector search
- `src/app/tools/discountLogic.py` -- Customer discount calculation (simulated DB + LLM logic)
- `src/app/tools/imageCreationTool.py` -- Image generation
- `src/app/tools/understandImage.py` / `imageUnderstandingTool.py` -- Phi-4 vision model image analysis
- `src/app/tools/inventoryCheck.py` -- Inventory lookup

### Utilities

- `src/utils/env_utils.py` -- Environment variable loading/validation
- `src/utils/history_utils.py` -- Chat history formatting, redaction, parsing
- `src/utils/response_utils.py` -- Agent response parsing (structured JSON extraction)
- `src/utils/message_utils.py` -- Rotating UI messages, fast JSON serialization (orjson)
- `src/utils/storage_utils.py` -- Azure Blob Storage operations

### Observability

OpenTelemetry tracing via `azure-monitor-opentelemetry` sending to Application Insights. Functions decorated with `@trace_function()`. The `APPLICATIONINSIGHTS_CONNECTION_STRING` env var is required.

## Branch Strategy

Workshop exercises use branches like `ex-01`, `ex-02`, `ex-03`, `ex-04` etc. Main branch is `main`.

## Key Conventions

- Agent IDs in env vars match domain names used in `HandoffService.AGENT_DOMAINS` (e.g., `cora`, `cart_manager`, `interior_designer`)
- Agent responses are structured JSON with fields: `answer`, `products`, `discount_percentage`, `image_url`, `additional_data`, `cart`
- Session state (cart, discount, loyalty) persists per WebSocket connection
- Image descriptions are cached per session to avoid re-analysis
- `orjson` is used instead of `json` for performance-critical serialization
