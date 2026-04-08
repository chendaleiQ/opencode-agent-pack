---
name: change-triage
description: Leader-only skill. Run before any implementation. Outputs structured JSON for lane, tier, and minimal execution-path routing. Must not be invoked by analyzer, implementer, or reviewer.
---

# Skill: change-triage（V5）

## Purpose

Run before any implementation.
Output stable structured JSON with:

- task type
- complexity/risk
- sensitive flags
- lane
- tier strategy
- minimal execution controls

## Mandatory Rules

- triage must run first
- no implementation before triage
- output exactly one JSON object
- fixed field names only
- no extra fields
- `finalApprovalTier` must always be `tier_top`

## Fixed Output Format

{
"taskType": "feature|bugfix|refactor|review|investigation",
"complexity": "low|high",
"risk": "low|high",
"touchesAuth": false,
"touchesDbSchema": false,
"touchesPublicApi": false,
"touchesDestructiveAction": false,
"estimatedFiles": 1,
"lane": "quick|standard|guarded|strict",
"delegate": true,
"needsPlan": false,
"needsReviewer": false,
"needsFinalApproval": true,
"analysisTier": "tier_fast|tier_mid|tier_top",
"executorTier": "tier_fast|tier_mid|tier_top",
"reviewTier": "tier_fast|tier_mid|tier_top",
"finalApprovalTier": "tier_top",
"reasoningSummary": "一句话说明为什么这么分流"
}

## Classification Rules

### taskType

- feature
- bugfix
- refactor
- review
- investigation

### complexity

- low: local, bounded, simple logic
- high: cross-module or non-trivial dependency/logic

### risk

- if any sensitive flag is true -> risk must be high
- otherwise evaluate impact, uncertainty, rollback cost

### sensitive flags

- touchesAuth
- touchesDbSchema
- touchesPublicApi
- touchesDestructiveAction

### estimatedFiles

- integer >= 1

## Lane Mapping

- quick: complexity=low, risk=low, all sensitive false, estimatedFiles<=2
- standard: complexity=high, risk=low
- guarded: complexity=low, risk=high
- strict: complexity=high, risk=high
- unstable/unclear classification: strict

## needsPlan

- quick=false
- standard=true
- guarded=false
- strict=true

## delegate

- quick: true, but only dispatch the minimal required downstream role for the task shape
- standard/guarded/strict: true

## needsReviewer

- quick: false by default; set true only for review tasks, explicit review requests, or when execution reveals risk/verify uncertainty
- standard/guarded/strict: true

## Quick Minimal Path Rule

- quick implementation work: dispatch `implementer` only
- quick investigation work: dispatch `analyzer` only
- quick review work: dispatch `reviewer` only
- do not dispatch analyzer + implementer + reviewer as a fixed chain for quick by default
- if quick needs multiple downstream roles to finish stably, escalate instead of forcing a full quick chain

## Subagent Handoff Rule

- `change-triage` is leader-only
- delegated subagents must consume the handoff and stay in-role
- delegated subagents must not rerun triage or re-enter the full workflow on their own
- when a subagent lacks boundary clarity, it should report back for escalation rather than invoking heavyweight workflow skills

## Tier Defaults

### quick

- analysisTier=tier_fast
- executorTier=tier_fast
- reviewTier=tier_mid (only when reviewer is needed)
- finalApprovalTier=tier_top

### standard

- analysisTier=tier_fast or tier_mid
- executorTier=tier_fast or tier_mid
- reviewTier=tier_mid
- finalApprovalTier=tier_top

### guarded

- analysisTier=tier_mid
- executorTier=tier_mid or tier_fast
- reviewTier=tier_mid
- finalApprovalTier=tier_top

### strict

- analysisTier=tier_mid or tier_top
- executorTier=tier_mid
- reviewTier=tier_top or tier_mid
- finalApprovalTier=tier_top

## Consistency Constraints

- strict cannot be tier_fast-led
- sensitive-hit tasks cannot route to quick/standard
- finalApprovalTier always tier_top
