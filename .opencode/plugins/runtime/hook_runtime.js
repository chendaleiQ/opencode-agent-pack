import {
  buildBlockedCompletionMessage,
  buildSystemGuard,
  classifyVerificationCommand,
  collectFilePaths,
  detectClosureAttempt,
  evaluateCloseGate,
  extractTextParts,
  isNoVerifyCommand,
  isProtectedConfigPath,
  parsePlanningArtifactFromText,
  parseManualVerificationFromText,
  parseReviewerFromText,
  parseTriageFromText,
  parseVerificationFailureFromToolResult,
  parseVerificationFailureFromText,
} from './evidence_gate.js';
import { appendAuditRecord } from './audit_store.js';
import {
  childSessionIDFromOutput,
  classifyPlanningQuestionDecision,
  enforceTriageBeforeExecution,
  isFileMutationTool,
  isLeaderManagedSession,
  isPlanningDecisionQuestion,
  maybeRecordReviewerEscalation,
  planningArtifactKindForPath,
} from './hook_runtime_helpers.js';
import { getProfileFeatures } from './profiles.js';
import {
  loadState,
  markClosable,
  markClosed,
  mergeChildSessionState,
  recordCompletionAttempt,
  recordEditedFile,
  recordLatestUserMessage,
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
} from './state_store.js';

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
      audit(runtime, { type: 'chat.message', sessionID: input.sessionID, agent: input.agent || 'leader' });
    },

    'tool.execute.before': async (input, output) => {
      const context = enforceTriageBeforeExecution({ buildContext, audit }, runtime, input.sessionID, 'tool', input.tool, output.args || {});
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
          const failureNote = parseVerificationFailureFromToolResult(output);
          if (failureNote) {
            recordVerificationFailure(context, category, command, output.title || 'bash', failureNote);
          } else {
            recordVerification(context, category, command, output.title || 'bash');
          }
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
      enforceTriageBeforeExecution({ buildContext, audit }, runtime, input.sessionID, 'command', input.command, { arguments: input.arguments });
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
      if (verificationFailure) recordVerificationFailure(context, 'unknown', '', 'verification failed', verificationFailure);

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
