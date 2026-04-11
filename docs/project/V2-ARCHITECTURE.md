# OpenCode V2 Architecture Blueprint

## Scope

This document defines the target architecture for the OpenCode-only V2 line.

V2 is **not** a multi-entry ECC-style orchestration system. It keeps do-the-thing's original design goal:

- one strongest entry: `leader`
- single workflow owner
- explicit lane+tier routing
- bounded subagent delegation
- hard close authority at `tier_top`

V2 adds a stronger execution layer around that model.

## Core Definition

V2 is a **leader-first, state-machine-centered, hook-enforced workflow system**.

That means:

- `leader` owns workflow decisions
- workflow state is the source of truth
- hooks enforce execution-time guarantees
- method skills improve reasoning quality but do not own workflow control
- subagents execute within handoff boundaries only

## Architecture Layers

### 1. Workflow Control Layer

Owned by `leader`.

Responsibilities:

- intake
- triage
- lane selection
- tier selection
- escalation
- final approval

### 2. Workflow State Layer

The state layer stores the task truth model.

Representative fields:

- `entryType`
- `phase`
- `lane`
- `tiers`
- `riskFlags`
- `estimatedFiles`
- `editedFiles`
- `reviewStatus`
- `verificationStatus`
- `closeEligibility`

### 3. Hook Runtime Layer

Hooks are the execution guarantee layer.

Responsibilities:

- tool blocking
- protected-config blocking
- edited-file accumulation
- evidence capture
- evidence staleness tracking
- audit logging
- close-time gating
- session persistence and recovery
- stop/pre-compact lifecycle handling

Hooks do **not** decide lane, tier, or final closure.

### 4. Method Skill Layer

Built-in `dtt-*` skills remain the method layer.

Responsibilities:

- triage method
- brainstorming
- planning
- debugging
- TDD discipline
- review framing
- verification discipline
- branch finishing

Skills improve reasoning, but they are not the system of record.

### 5. Execution Role Layer

Delegated roles stay bounded:

- `analyzer`
- `implementer`
- `reviewer`

They consume leader handoff and must not take workflow ownership.

## Primary Flow

```text
User
  -> leader
  -> workflow state machine
  -> hook enforcement
  -> bounded subagent execution
  -> verification gate
  -> leader final approval
```

## Core Contracts

V2 depends on five contracts:

1. workflow state schema
2. hook lifecycle contract
3. evidence schema
4. audit schema
5. close gate contract

## Hook vs Skill Boundary

### Hooks own

- deterministic lifecycle actions
- hard blocks
- state updates
- evidence recording
- audit writes
- close gates

### Skills own

- reasoning quality
- method choice inside workflow
- planning depth
- debugging structure
- review structure

## V2 Completion Criteria

OpenCode V2 should only be considered complete when:

1. all tasks land in explicit workflow phases
2. all important lifecycle points are hook-backed
3. close attempts require fresh evidence
4. workflow state persists and can recover forward safely
5. audit logs provide both event history and task summaries
6. leader remains the only closure authority

## Relationship to V1

The current installer defaults OpenCode users to the final pre-hooks V1 release.

That keeps the stable single-entry workflow available while V2 architecture is documented and developed separately.
