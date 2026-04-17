import fs from 'fs';

import { latestStatePath, sessionStatePath } from './paths.js';
import { profileFromLane } from './profiles.js';

function now() {
  return new Date().toISOString();
}

function phaseEntry(phase, reason) {
  return {
    at: now(),
    phase,
    reason,
  };
}

function evidenceEntry(kind, payload = {}) {
  return {
    at: now(),
    kind,
    ...payload,
  };
}

function createPlanningGate(enabled = false) {
  return {
    enabled,
    blockedStage: enabled ? 'spec' : null,
    specStatus: enabled ? 'required' : 'not_required',
    planStatus: enabled ? 'required' : 'not_required',
    specArtifacts: [],
    planArtifacts: [],
    approvals: [],
    decisions: [],
    pendingQuestions: [],
  };
}

function deriveBlockedStage(planningGate) {
  if (!planningGate?.enabled) return null;
  if (planningGate.specStatus !== 'approved') return 'spec';
  if (planningGate.planStatus !== 'approved') return 'plan';
  return null;
}

function normalizePlanningGate(planningGate, needsPlan = false) {
  const base = createPlanningGate(Boolean(needsPlan));
  const next = {
    ...base,
    ...(planningGate || {}),
    enabled: Boolean(needsPlan || planningGate?.enabled),
    specArtifacts: Array.isArray(planningGate?.specArtifacts) ? planningGate.specArtifacts : [],
    planArtifacts: Array.isArray(planningGate?.planArtifacts) ? planningGate.planArtifacts : [],
    approvals: Array.isArray(planningGate?.approvals) ? planningGate.approvals : [],
    decisions: Array.isArray(planningGate?.decisions) ? planningGate.decisions : [],
    pendingQuestions: Array.isArray(planningGate?.pendingQuestions) ? planningGate.pendingQuestions : [],
  };

  if (!next.enabled) {
    return createPlanningGate(false);
  }

  if (!next.specStatus || next.specStatus === 'not_required') next.specStatus = 'required';
  if (!next.planStatus || next.planStatus === 'not_required') next.planStatus = 'required';
  next.blockedStage = deriveBlockedStage(next);
  return next;
}

export function hasValidTriage(state) {
  return Boolean(
    state?.triage?.lane
      && state?.triage?.complexity
      && state?.triage?.risk
      && state?.triage?.finalApprovalTier,
  );
}

export function inferEntryTypeFromText(text) {
  const normalized = String(text || '').toLowerCase();
  if (!normalized.trim()) return 'general';
  if (/(close|finish|merge|pr|pull request|ship|release|收尾|完成收口)/.test(normalized)) return 'close';
  if (/(review|code review|审查|复查)/.test(normalized)) return 'review';
  if (/(debug|debugging|bug|fix failing|排查|调试|报错|失败)/.test(normalized)) return 'debug';
  if (/(implement|build|add|change|modify|refactor|实现|修改|新增|重构)/.test(normalized)) return 'implement';
  if (/(question|explain|how does|what is|为什么|是什么|怎么)/.test(normalized)) return 'chat';
  return 'general';
}

export function transitionPhase(context, nextPhase, reason) {
  return updateState(context, (state) => {
    if (state.phase === nextPhase) {
      state.phaseReason = reason;
      return state;
    }
    state.phase = nextPhase;
    state.phaseReason = reason;
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry(nextPhase, reason)].slice(-20);
    return state;
  });
}

export function setEntryType(context, entryType, reason = null) {
  return updateState(context, (state) => {
    state.entryType = entryType;
    if (reason) state.entryReason = reason;
    return state;
  });
}

export function createInitialState({ sessionID, projectKey }) {
  const timestamp = now();
  return {
    version: 1,
    sessionID,
    projectKey,
    status: 'active',
    profile: 'standard',
    entryType: 'general',
    entryReason: null,
    phase: 'created',
    phaseReason: 'session created',
    phaseHistory: [
      {
        at: timestamp,
        phase: 'created',
        reason: 'session created',
      },
    ],
    createdAt: timestamp,
    updatedAt: timestamp,
    latestUserMessage: null,
    lastEditAt: null,
    triage: null,
    planningGate: createPlanningGate(false),
    evidence: {
      triage: [],
      review: [],
      verification: [],
      manual: [],
      escalation: [],
    },
    reviewer: {
      required: false,
      status: 'missing',
      findings: [],
      updatedAt: null,
    },
    verification: {
      status: 'missing',
      commands: [],
      categories: [],
      manualChecks: [],
      pendingCommand: null,
      lastRunAt: null,
    },
    editedFiles: [],
    protectedBlocks: [],
    toolCalls: [],
    completion: {
      attempted: 0,
      blocked: 0,
      lastAttemptAt: null,
      lastBlockReason: null,
    },
  };
}

function readJson(filePath) {
  if (!fs.existsSync(filePath)) return null;
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function writeJson(filePath, data) {
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, 'utf-8');
}

function dedupeObjects(items) {
  const seen = new Set();
  const deduped = [];
  for (const item of items) {
    const key = JSON.stringify(item);
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(item);
  }
  return deduped;
}

export function loadState({ configDir, projectKey, sessionID }) {
  const state = readJson(sessionStatePath(configDir, projectKey, sessionID));
  if (!state) return createInitialState({ sessionID, projectKey });
  return {
    ...state,
    planningGate: normalizePlanningGate(state.planningGate, state.triage?.needsPlan),
  };
}

export function saveState({ configDir, projectKey, sessionID }, state) {
  const next = {
    ...state,
    updatedAt: now(),
  };
  writeJson(sessionStatePath(configDir, projectKey, sessionID), next);
  writeJson(latestStatePath(configDir, projectKey), next);
  return next;
}

export function updateState(context, updater) {
  const current = loadState(context);
  const next = updater(structuredClone(current)) || current;
  return saveState(context, next);
}

export function appendUnique(items, value) {
  if (value == null || value === '') return items;
  return items.includes(value) ? items : [...items, value];
}

export function recordEditedFile(context, filePath) {
  return updateState(context, (state) => {
    state.editedFiles = appendUnique(state.editedFiles, filePath);
    state.lastEditAt = now();
    if (['passed', 'manual_passed'].includes(state.verification.status)) {
      state.verification.status = 'stale';
    }
    if (state.phase !== 'closed' && hasValidTriage(state)) {
      state.phase = 'implementing';
      state.phaseReason = `edited file: ${filePath}`;
      state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('implementing', `edited file: ${filePath}`)].slice(-20);
    }
    return state;
  });
}

export function recordProtectedBlock(context, filePath) {
  return updateState(context, (state) => {
    state.protectedBlocks = appendUnique(state.protectedBlocks, filePath);
    return state;
  });
}

export function recordToolCall(context, entry) {
  return updateState(context, (state) => {
    const nextEntry = { at: now(), ...entry };
    state.toolCalls = [...state.toolCalls.slice(-24), nextEntry];
    return state;
  });
}

export function recordLatestUserMessage(context, message) {
  return updateState(context, (state) => {
    state.latestUserMessage = message;
    const inferred = inferEntryTypeFromText(message?.text || '');
    state.entryType = inferred;
    state.entryReason = 'latest user message';
    return state;
  });
}

export function recordTriage(context, triage) {
  return updateState(context, (state) => {
    state.triage = triage;
    state.planningGate = normalizePlanningGate(state.planningGate, triage?.needsPlan);
    state.profile = profileFromLane(triage?.lane);
    state.evidence.triage = [
      ...state.evidence.triage,
      evidenceEntry('triage', {
        lane: triage?.lane,
        complexity: triage?.complexity,
        risk: triage?.risk,
        needsReviewer: Boolean(triage?.needsReviewer),
      }),
    ].slice(-10);
    state.phase = 'triaged';
    state.phaseReason = `triage recorded: ${triage?.lane || 'unknown'}`;
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('triaged', `triage recorded: ${triage?.lane || 'unknown'}`)].slice(-20);
    state.reviewer.required = Boolean(triage?.needsReviewer);
    if (!triage?.needsReviewer) {
      state.reviewer.status = 'not_required';
    }
    return state;
  });
}

export function recordPlanningArtifact(context, artifactType, summary) {
  return updateState(context, (state) => {
    state.planningGate = normalizePlanningGate(state.planningGate, state.triage?.needsPlan);
    if (!state.planningGate.enabled) return state;

    const entry = {
      at: now(),
      kind: artifactType,
      summary,
    };

    if (artifactType === 'spec') {
      state.planningGate.specArtifacts = [...state.planningGate.specArtifacts, entry].slice(-10);
      if (state.planningGate.specStatus !== 'approved') state.planningGate.specStatus = 'drafted';
    }

    if (artifactType === 'plan') {
      state.planningGate.planArtifacts = [...state.planningGate.planArtifacts, entry].slice(-10);
      if (state.planningGate.planStatus !== 'approved') state.planningGate.planStatus = 'drafted';
    }

    state.planningGate.blockedStage = deriveBlockedStage(state.planningGate);
    return state;
  });
}

export function recordPlanningApproval(context, artifactType, note) {
  return updateState(context, (state) => {
    state.planningGate = normalizePlanningGate(state.planningGate, state.triage?.needsPlan);
    if (!state.planningGate.enabled) return state;

    const hasArtifact = artifactType === 'spec'
      ? state.planningGate.specArtifacts.length > 0
      : state.planningGate.planArtifacts.length > 0;
    if (!hasArtifact) return state;

    if (artifactType === 'spec') state.planningGate.specStatus = 'approved';
    if (artifactType === 'plan') state.planningGate.planStatus = 'approved';
    state.planningGate.approvals = [
      ...state.planningGate.approvals,
      { at: now(), kind: artifactType, note },
    ].slice(-10);
    state.planningGate.blockedStage = deriveBlockedStage(state.planningGate);
    return state;
  });
}

function summarizeQuestions(questions = []) {
  return questions.map((question) => ({
    header: question?.header || '',
    question: question?.question || '',
    options: Array.isArray(question?.options)
      ? question.options.map((option) => option?.label || '').filter(Boolean)
      : [],
  }));
}

function removePendingQuestion(pendingQuestions = [], requestID) {
  if (!requestID) return pendingQuestions;
  return pendingQuestions.filter((item) => item?.requestID !== requestID);
}

export function recordPlanningQuestion(context, requestID, artifactType, questions = []) {
  return updateState(context, (state) => {
    state.planningGate = normalizePlanningGate(state.planningGate, state.triage?.needsPlan);
    if (!state.planningGate.enabled || !requestID || !['spec', 'plan'].includes(artifactType)) return state;

    const entry = {
      at: now(),
      requestID,
      kind: artifactType,
      questions: summarizeQuestions(questions),
    };
    state.planningGate.pendingQuestions = [
      ...removePendingQuestion(state.planningGate.pendingQuestions, requestID),
      entry,
    ].slice(-10);
    return state;
  });
}

export function recordPlanningDecision(context, decision) {
  return updateState(context, (state) => {
    state.planningGate = normalizePlanningGate(state.planningGate, state.triage?.needsPlan);
    if (!state.planningGate.enabled) return state;

    const pending = (state.planningGate.pendingQuestions || [])
      .find((item) => item?.requestID === decision?.requestID);
    const artifactType = decision?.artifactType || pending?.kind || state.planningGate.blockedStage;
    if (!['spec', 'plan'].includes(artifactType)) return state;

    const normalizedDecision = decision?.decision === 'approved'
      ? 'approved'
      : decision?.decision === 'rejected'
        ? 'rejected'
        : 'changes_requested';
    const note = decision?.note || '';
    const entry = {
      at: now(),
      requestID: decision?.requestID || null,
      kind: artifactType,
      decision: normalizedDecision,
      note,
      answers: Array.isArray(decision?.answers) ? decision.answers : [],
    };
    state.planningGate.decisions = [...state.planningGate.decisions, entry].slice(-20);
    state.planningGate.pendingQuestions = removePendingQuestion(
      state.planningGate.pendingQuestions,
      decision?.requestID,
    );

    if (normalizedDecision === 'approved') {
      const hasArtifact = artifactType === 'spec'
        ? state.planningGate.specArtifacts.length > 0
        : state.planningGate.planArtifacts.length > 0;
      if (hasArtifact) {
        if (artifactType === 'spec') state.planningGate.specStatus = 'approved';
        if (artifactType === 'plan') state.planningGate.planStatus = 'approved';
        state.planningGate.approvals = [
          ...state.planningGate.approvals,
          { at: now(), kind: artifactType, note },
        ].slice(-10);
      }
    } else if (artifactType === 'spec' && state.planningGate.specStatus !== 'approved') {
      state.planningGate.specStatus = normalizedDecision;
    } else if (artifactType === 'plan' && state.planningGate.planStatus !== 'approved') {
      state.planningGate.planStatus = normalizedDecision;
    }

    state.planningGate.blockedStage = deriveBlockedStage(state.planningGate);
    return state;
  });
}

export function recordReviewerResult(context, reviewer) {
  return updateState(context, (state) => {
    state.reviewer.required = true;
    state.entryType = state.entryType === 'general' ? 'review' : state.entryType;
    state.reviewer.updatedAt = now();
    state.reviewer.findings = reviewer.findings || [];
    const hasHigh = (reviewer.findings || []).some((item) => item?.severity === 'high');
    const specPass = reviewer.specCompliance === 'pass';
    const qualityPass = reviewer.codeQuality === 'pass';
    state.reviewer.status = specPass && qualityPass && !hasHigh ? 'passed' : 'failed';
    state.evidence.review = [
      ...state.evidence.review,
      evidenceEntry('review', {
        status: state.reviewer.status,
        specCompliance: reviewer.specCompliance,
        codeQuality: reviewer.codeQuality,
        findings: reviewer.findings || [],
      }),
    ].slice(-10);
    state.phase = 'reviewing';
    state.phaseReason = `review result: ${state.reviewer.status}`;
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('reviewing', `review result: ${state.reviewer.status}`)].slice(-20);
    return state;
  });
}

export function mergeChildSessionState(context, childSessionID) {
  if (!childSessionID || childSessionID === context.sessionID) return loadState(context);
  const childState = readJson(sessionStatePath(context.configDir, context.projectKey, childSessionID));
  if (!childState) return loadState(context);

  return updateState(context, (state) => {
    state.editedFiles = [...new Set([...(state.editedFiles || []), ...(childState.editedFiles || [])])];
    if (!state.lastEditAt || (childState.lastEditAt && childState.lastEditAt > state.lastEditAt)) {
      state.lastEditAt = childState.lastEditAt || state.lastEditAt;
    }

    for (const key of ['triage', 'review', 'verification', 'manual', 'escalation']) {
      state.evidence[key] = dedupeObjects([
        ...(state.evidence[key] || []),
        ...(childState.evidence?.[key] || []),
      ]).slice(-20);
    }

    if (!state.triage && childState.triage) {
      state.triage = childState.triage;
      state.profile = childState.profile || state.profile;
    }

    state.planningGate = normalizePlanningGate(state.planningGate, state.triage?.needsPlan);
    const childPlanningGate = normalizePlanningGate(childState.planningGate, childState.triage?.needsPlan);
    if (childPlanningGate.enabled) {
      state.planningGate.enabled = true;
      state.planningGate.specStatus = childPlanningGate.specStatus === 'approved'
        ? 'approved'
        : state.planningGate.specStatus;
      state.planningGate.planStatus = childPlanningGate.planStatus === 'approved'
        ? 'approved'
        : (childPlanningGate.planArtifacts.length > 0 && state.planningGate.planStatus !== 'approved'
            ? 'drafted'
            : state.planningGate.planStatus);
      if (childPlanningGate.specArtifacts.length > 0 && state.planningGate.specStatus !== 'approved') {
        state.planningGate.specStatus = 'drafted';
      }
      state.planningGate.specArtifacts = dedupeObjects([
        ...state.planningGate.specArtifacts,
        ...childPlanningGate.specArtifacts,
      ]).slice(-20);
      state.planningGate.planArtifacts = dedupeObjects([
        ...state.planningGate.planArtifacts,
        ...childPlanningGate.planArtifacts,
      ]).slice(-20);
      state.planningGate.approvals = dedupeObjects([
        ...state.planningGate.approvals,
        ...childPlanningGate.approvals,
      ]).slice(-20);
      state.planningGate.decisions = dedupeObjects([
        ...state.planningGate.decisions,
        ...childPlanningGate.decisions,
      ]).slice(-20);
      state.planningGate.pendingQuestions = dedupeObjects([
        ...state.planningGate.pendingQuestions,
        ...childPlanningGate.pendingQuestions,
      ]).slice(-20);
      state.planningGate.blockedStage = deriveBlockedStage(state.planningGate);
    }

    const childReviewerUpdated = childState.reviewer?.updatedAt || null;
    const parentReviewerUpdated = state.reviewer?.updatedAt || null;
    if (childReviewerUpdated && (!parentReviewerUpdated || childReviewerUpdated >= parentReviewerUpdated)) {
      state.reviewer = {
        ...state.reviewer,
        ...childState.reviewer,
      };
      state.phase = 'reviewing';
      state.phaseReason = `merged reviewer result from ${childSessionID}`;
      state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('reviewing', `merged reviewer result from ${childSessionID}`)].slice(-20);
    }

    const childVerificationAt = childState.verification?.lastRunAt || null;
    const parentVerificationAt = state.verification?.lastRunAt || null;
    if (childVerificationAt && (!parentVerificationAt || childVerificationAt >= parentVerificationAt)) {
      state.verification = {
        ...state.verification,
        ...childState.verification,
        commands: dedupeObjects([
          ...(state.verification?.commands || []),
          ...(childState.verification?.commands || []),
        ]).slice(-20),
        categories: [...new Set([...(state.verification?.categories || []), ...(childState.verification?.categories || [])])],
        manualChecks: dedupeObjects([
          ...(state.verification?.manualChecks || []),
          ...(childState.verification?.manualChecks || []),
        ]).slice(-20),
      };
      if (state.phase !== 'reviewing') {
        state.phase = 'verifying';
        state.phaseReason = `merged verification from ${childSessionID}`;
        state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('verifying', `merged verification from ${childSessionID}`)].slice(-20);
      }
    }

    return state;
  });
}

export function recordVerification(context, category, command, title) {
  return updateState(context, (state) => {
    state.verification.status = 'passed';
    state.verification.lastRunAt = now();
    state.verification.pendingCommand = null;
    state.verification.categories = appendUnique(state.verification.categories, category);
    state.verification.commands = [...state.verification.commands, { category, command, title, at: now() }].slice(-20);
    state.evidence.verification = [
      ...state.evidence.verification,
      evidenceEntry('verification', {
        status: 'passed',
        category,
        command,
        title,
      }),
    ].slice(-20);
    state.phase = 'verifying';
    state.phaseReason = `verification passed: ${category}`;
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('verifying', `verification passed: ${category}`)].slice(-20);
    return state;
  });
}

export function recordVerificationStart(context, category, command) {
  return updateState(context, (state) => {
    state.verification.status = 'pending';
    state.verification.pendingCommand = { category, command, at: now() };
    state.phase = 'verifying';
    state.phaseReason = `verification started: ${category}`;
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('verifying', `verification started: ${category}`)].slice(-20);
    return state;
  });
}

export function recordManualVerification(context, note) {
  return updateState(context, (state) => {
    state.verification.status = 'manual_passed';
    state.verification.pendingCommand = null;
    state.verification.lastRunAt = now();
    state.verification.manualChecks = [...state.verification.manualChecks, { note, at: now() }].slice(-10);
    state.evidence.manual = [
      ...state.evidence.manual,
      evidenceEntry('manual', {
        status: 'passed',
        note,
      }),
    ].slice(-20);
    state.phase = 'verifying';
    state.phaseReason = 'manual verification recorded';
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('verifying', 'manual verification recorded')].slice(-20);
    return state;
  });
}

export function recordVerificationFailure(context, note) {
  return updateState(context, (state) => {
    state.verification.status = 'failed';
    state.verification.pendingCommand = null;
    state.verification.lastRunAt = now();
    state.verification.manualChecks = [...state.verification.manualChecks, { note: `FAILED: ${note}`, at: now() }].slice(-10);
    state.evidence.verification = [
      ...state.evidence.verification,
      evidenceEntry('verification', {
        status: 'failed',
        category: 'unknown',
        note,
      }),
    ].slice(-20);
    state.phase = 'verifying';
    state.phaseReason = 'verification failed';
    state.phaseHistory = [...(state.phaseHistory || []), phaseEntry('verifying', 'verification failed')].slice(-20);
    return state;
  });
}

export function markClosable(context, reason = 'close gate satisfied') {
  return transitionPhase(context, 'closable', reason);
}

export function markClosed(context, reason = 'closed by runtime') {
  return transitionPhase(context, 'closed', reason);
}

export function recordEscalationEvidence(context, reason, fromLane = null, toLane = null) {
  return updateState(context, (state) => {
    state.evidence.escalation = [
      ...state.evidence.escalation,
      evidenceEntry('escalation', { reason, fromLane, toLane }),
    ].slice(-10);
    return state;
  });
}

export function recordCompletionAttempt(context, allowed, missing) {
  return updateState(context, (state) => {
    state.completion.attempted += 1;
    state.completion.lastAttemptAt = now();
    state.completion.lastBlockReason = missing.length > 0 ? missing.join('; ') : null;
    if (!allowed) state.completion.blocked += 1;
    return state;
  });
}
