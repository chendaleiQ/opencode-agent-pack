import {
  buildBlockedCompletionMessage,
  buildSystemGuard,
  classifyVerificationCommand,
  collectFilePaths,
  detectClosureAttempt,
  evaluateCloseGate,
  extractTextParts,
  isNoVerifyCommand,
  isPlanningApprovalMessage,
  isProtectedConfigPath,
  parsePlanningArtifactFromText,
  parseManualVerificationFromText,
  parseReviewerFromText,
  parseTriageFromText,
  parseVerificationFailureFromText,
} from './evidence_gate.js';
import { appendAuditRecord } from './audit_store.js';
import { getProfileFeatures } from './profiles.js';
import {
  hasValidTriage,
  loadState,
  markClosable,
  markClosed,
  mergeChildSessionState,
  recordCompletionAttempt,
  recordEditedFile,
  recordEscalationEvidence,
  recordLatestUserMessage,
  recordPlanningApproval,
  recordPlanningArtifact,
  recordPlanningDecision,
  recordPlanningQuestion,
  recordManualVerification,
  recordProtectedBlock,
  recordReviewerResult,
  recordToolCall,
  recordTriage,
  recordVerification,
  recordVerificationFailure,
  recordVerificationStart,
  saveState,
  transitionPhase,
} from './state_store.js';

function isAllowedPreTriageTool(toolName, args) {
  if (['glob', 'grep', 'read'].includes(toolName)) return true;
  if (toolName !== 'skill') return false;
  return ['using-superpowers', 'dtt-change-triage'].includes(args?.name);
}

function isLeaderManagedSession(state) {
  const agent = state?.latestUserMessage?.agent || null;
  return !agent || agent === 'leader';
}

function planningArtifactKindForPath(filePath) {
  if (!filePath) return null;
  const normalized = String(filePath).replaceAll('\\', '/');
  if (/(^|\/)docs\/dtt\/specs\/[^/]+\.md$/i.test(normalized)) return 'spec';
  if (/(^|\/)docs\/dtt\/plans\/[^/]+\.md$/i.test(normalized)) return 'plan';
  return null;
}

function isFileMutationTool(toolName) {
  return ['write', 'edit', 'multiedit', 'apply_patch'].includes(toolName);
}

function flattenQuestionText(args) {
  const questions = Array.isArray(args?.questions) ? args.questions : [];
  return questions.flatMap((question) => [
    question?.header,
    question?.question,
    ...(Array.isArray(question?.options)
      ? question.options.flatMap((option) => [option?.label, option?.description])
      : []),
  ]).filter(Boolean).join(' ');
}

function isPlanningDecisionQuestion(args, blockedStage) {
  if (!blockedStage) return false;
  const text = flattenQuestionText(args);
  if (!text) return false;
  const stagePattern = blockedStage === 'spec'
    ? /(spec|规格)/i
    : /(plan|计划|方案)/i;
  const decisionPattern = /(批准|通过|同意|approve|approval|需要补充|补充|修改|调整|changes?|revise|拒绝|取消|reject|cancel)/i;
  return stagePattern.test(text) && decisionPattern.test(text);
}

function flattenAnswers(answers = []) {
  if (!Array.isArray(answers)) return [];
  return answers.flatMap((answer) => (Array.isArray(answer) ? answer : [answer]))
    .filter((item) => item != null && item !== '')
    .map((item) => String(item));
}

function classifyPlanningQuestionDecision(answers = [], rejected = false) {
  if (rejected) return { decision: 'rejected', note: 'question rejected', answers: [] };
  const labels = flattenAnswers(answers);
  const text = labels.join(' ').trim();
  if (!text) return { decision: 'changes_requested', note: '', answers: labels };
  if (/(拒绝|取消|终止|不批准|不通过|reject|cancel|stop)/i.test(text)) {
    return { decision: 'rejected', note: text, answers: labels };
  }
  if (/(批准|通过|同意|approve|approved)/i.test(text)) {
    return { decision: 'approved', note: text, answers: labels };
  }
  return { decision: 'changes_requested', note: text, answers: labels };
}

function enforceTriageBeforeExecution(runtime, sessionID, kind, name, args) {
  const context = buildContext(runtime, sessionID);
  const state = loadState(context);
  if (!isLeaderManagedSession(state)) return context;
  if (hasValidTriage(state)) return context;
  if (kind === 'tool' && isAllowedPreTriageTool(name, args)) return context;

  audit(runtime, {
    type: `${kind}.blocked`,
    sessionID,
    [kind]: name,
    reason: 'missing-triage',
  });
  throw new Error(`do-the-thing runtime blocked ${kind} execution: must run triage before execution`);
}

function buildContext(runtime, sessionID) {
  return {
    configDir: runtime.configDir,
    projectKey: runtime.projectKey,
    sessionID,
  };
}

function audit(runtime, record) {
  appendAuditRecord({ configDir: runtime.configDir, projectKey: runtime.projectKey }, record);
}

function ensureSessionState(runtime, sessionID) {
  const context = buildContext(runtime, sessionID);
  return saveState(context, loadState(context));
}

function activeFeatures(runtime, sessionID) {
  const context = buildContext(runtime, sessionID);
  const state = loadState(context);
  return getProfileFeatures(state.profile || 'standard');
}

function childSessionIDFromOutput(output) {
  return output?.metadata?.sessionID || output?.metadata?.sessionId || output?.sessionID || output?.sessionId || null;
}

const LANE_ORDER = ['quick', 'standard', 'guarded', 'strict'];

function laneRank(lane) {
  const index = LANE_ORDER.indexOf(lane);
  return index >= 0 ? index : -1;
}

function maybeRecordReviewerEscalation(context, reviewer) {
  const state = loadState(context);
  const fromLane = state?.triage?.lane || null;
  const toLane = reviewer?.recommendedLane || null;
  const stricterLaneRecommended = fromLane && toLane && laneRank(toLane) > laneRank(fromLane);
  const escalationRequested = Boolean(reviewer?.mustEscalate) || stricterLaneRecommended;
  if (!escalationRequested) return;

  const tierReason = reviewer?.recommendedTierUpgrade?.needed
    ? reviewer.recommendedTierUpgrade.reason || 'tier upgrade recommended'
    : null;
  const reason = stricterLaneRecommended
    ? `reviewer recommended escalation from ${fromLane} to ${toLane}`
    : `reviewer requested escalation${tierReason ? `: ${tierReason}` : ''}`;

  recordEscalationEvidence(context, reason, fromLane, toLane);
}

export function createRuntimeHooks(runtime) {
  return {
    event: async ({ event }) => {
      if (event?.type === 'session.created' && event.properties?.info?.id) {
        const sessionID = event.properties.info.id;
        ensureSessionState(runtime, sessionID);
        audit(runtime, { type: 'session.created', sessionID });
      }

      if (event?.type === 'session.compacted' && event.properties?.info?.id) {
        audit(runtime, { type: 'session.compacted', sessionID: event.properties.info.id });
      }

      if (event?.type === 'question.asked' && event.properties?.sessionID && event.properties?.id) {
        const context = buildContext(runtime, event.properties.sessionID);
        const state = loadState(context);
        const blockedStage = state?.planningGate?.blockedStage;
        if (
          isLeaderManagedSession(state)
          && state?.planningGate?.enabled
          && blockedStage
          && isPlanningDecisionQuestion(event.properties, blockedStage)
        ) {
          recordPlanningQuestion(
            context,
            event.properties.id,
            blockedStage,
            event.properties.questions || [],
          );
          audit(runtime, {
            type: 'question.planning-asked',
            sessionID: event.properties.sessionID,
            requestID: event.properties.id,
            blockedStage,
          });
        }
      }

      if (event?.type === 'question.replied' && event.properties?.sessionID && event.properties?.requestID) {
        const context = buildContext(runtime, event.properties.sessionID);
        const state = loadState(context);
        const pending = (state?.planningGate?.pendingQuestions || [])
          .find((item) => item?.requestID === event.properties.requestID);
        const artifactType = pending?.kind || state?.planningGate?.blockedStage;
        if (
          isLeaderManagedSession(state)
          && state?.planningGate?.enabled
          && ['spec', 'plan'].includes(artifactType)
        ) {
          const decision = classifyPlanningQuestionDecision(event.properties.answers || []);
          recordPlanningDecision(context, {
            requestID: event.properties.requestID,
            artifactType,
            ...decision,
          });
          audit(runtime, {
            type: 'question.planning-replied',
            sessionID: event.properties.sessionID,
            requestID: event.properties.requestID,
            artifactType,
            decision: decision.decision,
          });
        }
      }

      if (event?.type === 'question.rejected' && event.properties?.sessionID && event.properties?.requestID) {
        const context = buildContext(runtime, event.properties.sessionID);
        const state = loadState(context);
        const pending = (state?.planningGate?.pendingQuestions || [])
          .find((item) => item?.requestID === event.properties.requestID);
        if (isLeaderManagedSession(state) && state?.planningGate?.enabled && pending?.kind) {
          const decision = classifyPlanningQuestionDecision([], true);
          recordPlanningDecision(context, {
            requestID: event.properties.requestID,
            artifactType: pending.kind,
            ...decision,
          });
          audit(runtime, {
            type: 'question.planning-rejected',
            sessionID: event.properties.sessionID,
            requestID: event.properties.requestID,
            artifactType: pending.kind,
          });
        }
      }
    },

    'chat.message': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const text = extractTextParts(output.parts);
      const state = recordLatestUserMessage(context, {
        at: new Date().toISOString(),
        agent: input.agent || 'leader',
        messageID: input.messageID || null,
        text,
      });
      if (
        isLeaderManagedSession(state)
        && state?.planningGate?.enabled
        && state?.planningGate?.blockedStage
        && isPlanningApprovalMessage(text)
      ) {
        recordPlanningApproval(context, state.planningGate.blockedStage, text);
      }
      audit(runtime, { type: 'chat.message', sessionID: input.sessionID, agent: input.agent || 'leader' });
    },

    'tool.execute.before': async (input, output) => {
      const context = enforceTriageBeforeExecution(runtime, input.sessionID, 'tool', input.tool, output.args || {});
      const features = activeFeatures(runtime, input.sessionID);
      const args = output.args || {};

      if (features.noVerifyBlock && input.tool === 'bash' && isNoVerifyCommand(args.command || '')) {
        audit(runtime, { type: 'tool.blocked', sessionID: input.sessionID, tool: input.tool, reason: 'no-verify' });
        throw new Error('do-the-thing runtime blocked git commit --no-verify');
      }

      if (input.tool === 'bash') {
        const category = classifyVerificationCommand(args.command || '');
        if (category) {
          recordVerificationStart(context, category, args.command || '');
        }
      }

      if (features.protectedConfigBlock && isFileMutationTool(input.tool)) {
        for (const filePath of collectFilePaths(args)) {
          if (isProtectedConfigPath(filePath)) {
            recordProtectedBlock(context, filePath);
            audit(runtime, { type: 'tool.blocked', sessionID: input.sessionID, tool: input.tool, reason: 'protected-config', filePath });
            throw new Error(`do-the-thing runtime blocked protected config edit: ${filePath}`);
          }
        }
      }

      recordToolCall(context, { phase: 'before', tool: input.tool, args });
    },

    'tool.execute.after': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      recordToolCall(context, { phase: 'after', tool: input.tool, args: input.args, title: output.title });

      if (isFileMutationTool(input.tool)) {
        for (const filePath of collectFilePaths(input.args)) {
          const planningKind = planningArtifactKindForPath(filePath);
          if (planningKind) {
            recordPlanningArtifact(context, planningKind, `planning doc updated: ${filePath}`);
          } else {
            recordEditedFile(context, filePath);
          }
        }
      }

      if (input.tool === 'bash') {
        const command = input.args?.command || '';
        const category = classifyVerificationCommand(command);
        if (category) {
          recordVerification(context, category, command, output.title || 'bash');
        }
      }

      if (input.tool === 'task') {
        const childSessionID = childSessionIDFromOutput(output);
        if (childSessionID) {
          mergeChildSessionState(context, childSessionID);
        }
      }

      audit(runtime, {
        type: 'tool.after',
        sessionID: input.sessionID,
        tool: input.tool,
        title: output.title,
      });
    },

    'command.execute.before': async (input) => {
      enforceTriageBeforeExecution(runtime, input.sessionID, 'command', input.command, { arguments: input.arguments });
      audit(runtime, {
        type: 'command.execute.before',
        sessionID: input.sessionID,
        command: input.command,
      });
    },

    'experimental.chat.system.transform': async (input, output) => {
      if (!input.sessionID) return;
      const context = buildContext(runtime, input.sessionID);
      const state = loadState(context);
      if (!isLeaderManagedSession(state)) return;
      output.system.push(buildSystemGuard(state));
    },

    'experimental.session.compacting': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const state = loadState(context);
      if (!isLeaderManagedSession(state)) return;
      output.context.push(buildSystemGuard(state));
    },

    'experimental.text.complete': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const triage = parseTriageFromText(output.text);
      if (triage) recordTriage(context, triage);

      const planningArtifact = parsePlanningArtifactFromText(output.text);
      if (planningArtifact) recordPlanningArtifact(context, planningArtifact.kind, planningArtifact.summary);

      const reviewer = parseReviewerFromText(output.text);
      if (reviewer) {
        recordReviewerResult(context, reviewer);
        maybeRecordReviewerEscalation(context, reviewer);
      }

      const manualVerification = parseManualVerificationFromText(output.text);
      if (manualVerification) recordManualVerification(context, manualVerification);

      const verificationFailure = parseVerificationFailureFromText(output.text);
      if (verificationFailure) recordVerificationFailure(context, verificationFailure);

      const currentState = loadState(context);
      if (!isLeaderManagedSession(currentState)) return;

      const features = activeFeatures(runtime, input.sessionID);
      const gateOptions = {
        checkStaleness: features.evidenceStaleness,
        requireAllEvidence: features.requireAllEvidence,
      };

      if (features.closeGate) {
        const gatePreview = evaluateCloseGate({
          ...currentState,
          phase: 'closable',
        }, gateOptions);
        if (gatePreview.allowed) {
          markClosable(context, 'review and verification evidence satisfied');
        }
      }

      if (features.completionRewrite && detectClosureAttempt(output.text)) {
        const state = loadState(context);
        const gate = evaluateCloseGate(state, gateOptions);
        recordCompletionAttempt(context, gate.allowed, gate.missing);
        audit(runtime, {
          type: 'completion.attempt',
          sessionID: input.sessionID,
          allowed: gate.allowed,
          missing: gate.missing,
        });
        if (!gate.allowed) {
          output.text = buildBlockedCompletionMessage(state, gate.missing);
        } else {
          markClosed(context, 'completion attempt accepted');
        }
      }
    },
  };
}
