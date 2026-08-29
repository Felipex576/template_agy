# Synapse Protocol — Persistent Memory & Spec-Driven Development

A streamlined, zero-dependency engineering protocol focused on **Persistent Memory** and **Spec-Driven Development (SDD)**.

---

## The 3-Step Execution Lifecycle

Every AI agent operating in this repository follows this direct 3-step cycle:

```text
[User Request Received]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  STEP 1: LOAD MEMORY (Context Awareness)               │
│  - Read .synapse/memory/observations.json for prior    │
│    architectural decisions, conventions, and patterns. │
│  - Read .synapse/memory/sessions.csv for session log.  │
│  - Ensure proposed solutions do not violate memory.    │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  STEP 2: SPEC-DRIVEN DEVELOPMENT (SDD Workflow)        │
│  - For non-trivial tasks, fill/update:                 │
│    .synapse/sdd_spec.md                                │
│  - Define:                                             │
│    1. Proposal: Goal & Scope (in/out boundaries).      │
│    2. Requirements: Given-When-Then criteria.          │
│    3. Design: Affected layers, classes, and types.     │
│    4. Tasks: Sequential implementation task list.      │
│  - Implement code and execute unit tests.              │
└────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  STEP 3: SAVE LEARNINGS (Persistent Memory Update)     │
│  - Append new architectural patterns, conventions, or  │
│    bug solutions to .synapse/memory/observations.json. │
│  - Append a one-line summary to sessions.csv.          │
└────────────────────────────────────────────────────────┘
          │
          ▼
[Deliver Verified Response to User]
```

---

## Quick-Start Prompt for Any AI Agent

To activate Synapse in any session, provide this directive:

> *"Please read `.synapse/PROTOCOL.md`. Load persistent memory from `.synapse/memory/observations.json`, check prior decisions, and plan non-trivial changes in `.synapse/sdd_spec.md` before implementing."*
