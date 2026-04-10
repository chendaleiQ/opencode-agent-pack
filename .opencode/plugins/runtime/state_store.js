import fs from 'fs';

import { latestStatePath, sessionStatePath } from './paths.js';

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
    triage: null,
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

export function loadState({ configDir, projectKey, sessionID }) {
  const state = readJson(sessionStatePath(configDir, projectKey, sessionID));
  return state || createInitialState({ sessionID, projectKey });
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
    if (['passed', 'manual_passed'].includes(state.verification.status)) {
      state.verification.status = 'stale';
    }
    if (state.phase !== 'closed') {
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
