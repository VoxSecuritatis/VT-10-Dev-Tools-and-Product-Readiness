# Multi-Agent Workflow Planner for a Startup Accelerator

##### VT_AGI: Dev Tools & Product Readiness Module Project | Brock Frary | Published: 2026-07-19 | Updated: 2026-07-20

A startup domain (for example `fintech`) goes in; a founder-ready pitch deck outline comes out, produced by three collaborating LangGraph agents -- a Research Agent, a Funding Advisor, and a Pitch Coach -- that hand off state, revise on feedback, and log every transition for full reasoning traceability.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2.9-1C3C3C)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4.1--mini-412991?logo=openai&logoColor=white)
![Chroma](https://img.shields.io/badge/Chroma-vector%20memory-FF6F00)
![Azure](https://img.shields.io/badge/Azure-Application%20Insights%20(optional)-0078D4?logo=microsoftazure&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)

---

## Primary Project Artifact

### [Reflection: Multi-Agent Workflow Planner for a Startup Accelerator](./assets/reflection.pdf)

---

## About This Project

This is the module project for **VT_AGI: Dev Tools & Product Readiness**, part of the *Applied Agentic AI: Systems, Design & Impact* course at Virginia Tech.

The project implements a fixed, three-role agent pipeline -- Research Agent, Funding Advisor, Pitch Coach -- orchestrated with LangGraph's `StateGraph`. Agent hand-offs run over a single shared, typed state object, and a conditional edge gives the Pitch Coach a first-class way to route work back to an earlier agent when it judges the research or funding findings incomplete, capped at a fixed number of revisions so the loop always terminates.

Every node transition is logged locally as structured JSONL and, when configured, mirrored to Azure Application Insights as trace spans -- so the full reasoning path and every memory/context handoff between agents is reconstructable after the fact.

The primary technical decisions were around picking LangGraph over CrewAI/AutoGen for native cyclic-edge support, and scoping Azure to observability specifically rather than displacing an already-justified plain OpenAI API backend. Both are documented in detail in `reflection.pdf` and in the Key Design Decisions section below.

---

## Architecture

```text
startup domain
      |
      v
+-----------------+     +--------------------+     +----------------+
| Research Agent  | --> | Funding Advisor    | --> | Pitch Coach    |
| (market trends)  |     | (grants/funding)    |     | (outline +     |
+-----------------+     +--------------------+     | route decision)|
        ^                        ^                  +--------+-------+
        |                        |                           |
        +---- feedback loop -----+---------------------------+
                (capped at 2 revisions)
```

![End-to-end workflow diagram](./assets/diagram_workflow.jpg)

![Agent responsibility swimlane](./assets/diagram_swimlane.jpg)

- **Orchestration framework: LangGraph.** A `StateGraph` (`workflow/graph.py`) wires the three agents as nodes over a single shared, typed state object (`workflow/state.py`). LangGraph was chosen over CrewAI and AutoGen because its explicit state graph gives native conditional/cyclic edges -- the feedback loop is a first-class graph edge, not extra glue code -- and an explicit, typed state object that is inspectable at every node transition, which is exactly what the logging and reasoning-traceability requirement needs.
- **LLM backend:** OpenAI API (`langchain_openai.ChatOpenAI`, default model `gpt-4.1-mini`), configured once in `config.get_llm()` and reused by all three agents.
- **Vector memory:** a local Chroma collection (`memory/vector_store.py`), persisted under `data/chroma_store/`. Each agent's finding is stored keyed by domain and agent name, and retrieved as prior context on later runs (or later feedback-loop passes) for the same domain.
- **Observability:** every node transition is always logged locally as structured JSONL (`observability/trace_logger.py`, one line per transition in `logs/run_<run_id>.jsonl`). If `AZURE_APPINSIGHTS_CONNECTION_STRING` is set, the same transitions are also sent to Azure Application Insights as trace spans (`observability/azure_telemetry.py`); if it is not set, the code logs a single `[INFO]` line and continues -- Azure is never required for the project to run.
- **Interfaces:** a CLI (`interface/cli.py`) and a Jupyter/ipywidgets notebook GUI (`interface/notebook_gui.ipynb`), both calling the same `workflow.graph.run_workflow()` function so there is exactly one implementation of the workflow logic.

---

## Agent Roles and Responsibilities

| Agent | Responsibility | Reads | Writes |
|---|---|---|---|
| **Research Agent** | Gathers domain-specific market trends and insights | `domain`, `feedback_notes` | `research_findings` |
| **Funding Advisor** | Recommends grants and funding programs suited to the domain | `domain`, `research_findings`, `feedback_notes` | `funding_findings` |
| **Pitch Coach** | Synthesizes research and funding findings into a pitch deck outline; decides whether the workflow ends or loops back for more detail | `domain`, `research_findings`, `funding_findings`, `revision_count` | `pitch_outline`, `next_step`, `feedback_notes`, `revision_count` |

Responsibilities are scoped so there is no overlap: only the Research Agent produces market findings, only the Funding Advisor produces funding recommendations, and only the Pitch Coach writes the final outline or decides on a feedback loop.

---

## Coordination Flow and Feedback Loop

1. The Research Agent runs first, producing market trends and insights for the given domain.
2. The Funding Advisor runs next, reading the Research Agent's findings and producing funding recommendations grounded in them.
3. The Pitch Coach synthesizes both into a pitch deck outline (Problem, Solution, Market, Business Model, Funding Ask, Team, Traction), then appends a verdict line to its own response: `COMPLETE`, `NEEDS_MORE_RESEARCH: <reason>`, or `NEEDS_MORE_FUNDING: <reason>`.
4. If the verdict is `COMPLETE` (or the revision cap has been reached), the workflow ends and returns the outline.
5. Otherwise, the workflow routes back to the Research Agent or Funding Advisor with `feedback_notes` set to the Pitch Coach's stated reason, and both agents re-run (research, then funding, then the Pitch Coach again) with that feedback in their prompt. This is capped at `config.MAX_PITCH_REVISIONS` (2) revisions so the loop always terminates.

Every one of these steps is written to the trace log (and to Azure Application Insights, if configured) with the agent name, revision number, a summary of what it read, and what it wrote -- so the full reasoning path and every memory/context handoff between agents is reconstructable after the fact.

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration framework | LangGraph over CrewAI/AutoGen | Native conditional/cyclic edges make the feedback loop a first-class graph edge, not glue code; the typed state object is inspectable at every node transition, which the logging requirement needs |
| LLM backend | Plain OpenAI API, not Azure OpenAI | Existing OpenAI account and credits were already available -- the path of least friction for a hosted-API backend; Azure OpenAI would have been a technically viable drop-in but was a deliberate non-choice, not an oversight |
| Vector memory | Local Chroma over a managed vector DB | Zero external-service setup while still giving genuine semantic retrieval of prior agent findings, at a scale where a managed cloud vector DB would add credential overhead for no clear benefit |
| Interface | CLI + local Jupyter/ipywidgets notebook, not Colab | Keeps the course's demonstrated widget pattern (Textarea/Button/Output) but runs locally in VS Code's Jupyter extension; both entry points call the same `run_workflow()` so there is one implementation, not two |
| Observability scope | Azure Application Insights, optional | Scoped specifically to observability rather than displacing the already-justified plain OpenAI backend; degrades gracefully to local-only JSONL logging if not configured |
| Feedback-loop termination | Fixed revision cap (`MAX_PITCH_REVISIONS = 2`) | A cyclic graph needs a guaranteed exit condition; the cap bounds the loop regardless of what the model outputs, so termination does not depend on the model behaving well |
| Routing signal | Parsed verdict line, not a second structured-output call | Keeps the design to one call per agent; if the model omits the verdict line, the code defaults to ending the workflow rather than looping or erroring |

---

## Key Learnings

### Azure Portal no longer offers a classic-vs-workspace-based toggle

The original setup plan assumed a radio button for Application Insights resource mode. The current Portal UI has removed that choice -- it defaults straight to workspace-based, signaled only by a "Workspace Details" section that auto-selects a new Log Analytics Workspace. No action was needed beyond recognizing the UI had changed from what was expected.

### Chroma's default embedding model needs network access on first use

The first call to the vector store may need network access to download Chroma's default local embedding model; it is cached afterward. No API key or paid service is required for this, but it means the very first run is not fully offline even though the project has no other external dependency besides the OpenAI call itself.

### Live runs never triggered the feedback loop

Four live-LLM runs across three domains (fintech, urban vertical farming, telehealth for elder care) all returned `COMPLETE` on the first pass (`revision_count: 0`) -- `gpt-4.1-mini` consistently judged its own first-pass output sufficient. The feedback loop's correctness is verified through mocked tests that force a `NEEDS_MORE_*` verdict; it simply never fired under live conditions in this sample, which is a real observed limitation of relying on a single model's self-assessment rather than a forced test case.

---

## Tech Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| Orchestration | LangGraph | `1.2.9`; `StateGraph` with conditional/cyclic edges |
| LLM | OpenAI `gpt-4.1-mini` | via `langchain-openai` `1.3.5`, one call per agent per pass |
| Vector memory | Chroma | `1.5.9`; local persistent collection under `data/chroma_store/` |
| Observability | JSONL local logging + Azure Application Insights | `azure-monitor-opentelemetry` `1.8.9`; Azure is optional and degrades gracefully |
| Interfaces | CLI + Jupyter/ipywidgets notebook | `ipywidgets` `8.1.8`; both call the same `workflow.graph.run_workflow()` |
| Testing | pytest | `9.1.1`; all tests run against mocked OpenAI responses, no API key required |

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | `3.12+` on Windows |
| OpenAI API key | Standard OpenAI API key |
| OpenAI model | `gpt-4.1-mini` recommended |
| Azure Application Insights connection string | Optional -- leave blank to run entirely on local JSONL logging |

---

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`. `AZURE_APPINSIGHTS_CONNECTION_STRING` is optional -- leave it blank to run entirely on local logging (see Architecture above).

---

## Running the Demo

CLI:

```powershell
python -m interface.cli --domain fintech
```

This prints the pitch deck outline and reports where the trace log was written (`logs/run_<run_id>.jsonl`).

Notebook GUI (VS Code Jupyter extension): open `interface/notebook_gui.ipynb`, run all cells, enter a domain in the text box, and click **Generate Pitch Outline**. Both interfaces call the same `workflow.graph.run_workflow()` entry point -- no logic is duplicated between them.

---

## Running Tests

```powershell
pytest tests/
```

All agent, workflow, memory, and logging tests run against mocked OpenAI responses -- no API key or network access is required to run the test suite.

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (required) |
| `OPENAI_MODEL` | Model name; default is `gpt-4.1-mini` |
| `AZURE_APPINSIGHTS_CONNECTION_STRING` | Optional; enables Azure Application Insights trace spans alongside local JSONL logging |

Never commit `.env`. It is listed in `.gitignore`. Only `.env.example` is committed.

---

## Project Structure

```text
.
├── agents/                # Research Agent, Funding Advisor, Pitch Coach -- one OpenAI call each
├── workflow/               # LangGraph StateGraph wiring and the shared typed state object
├── memory/                 # Local Chroma vector store, keyed by domain and agent name
├── observability/          # Local JSONL trace logging + optional Azure Application Insights
├── interface/               # CLI entry point and Jupyter/ipywidgets notebook GUI
├── tests/                  # pytest suite, all agents mocked
├── config.py                # Environment variable names, model settings, shared get_llm()
├── requirements.txt         # Pinned direct dependencies
├── .env.example              # Variable names template; no secrets
├── README.md                 # Project README
└── assets/reflection.pdf      # Portfolio document with diagrams, design decisions,
                               # challenges, build walkthrough, and screenshots
```

---

## Portfolio Document

`reflection.pdf` is the full project narrative. It includes:

- End-to-end workflow diagram
- Three-lane agent responsibility swimlane diagram
- Design decisions and rationale
- Challenges encountered and how they were resolved
- Trade-offs table
- Personal reflections on the course, the LangGraph build, and the Azure observability setup
- Build walkthrough with annotated screenshots covering every project stage

---

## Copyright

© 2026 Brock Frary. All rights reserved.
