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
  "needsReviewer": true,
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

## Tier Defaults
### quick
- analysisTier=tier_fast
- executorTier=tier_fast
- reviewTier=tier_mid
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
