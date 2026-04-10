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
  parseManualVerificationFromText,
  parseReviewerFromText,
  parseTriageFromText,
  parseVerificationFailureFromText,
} from './evidence_gate.js';
import { appendAuditRecord } from './audit_store.js';
import { getProfileFeatures } from './profiles.js';
import {
  loadState,
  markClosable,
  markClosed,
  recordCompletionAttempt,
  recordEditedFile,
  recordLatestUserMessage,
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
    },

    'chat.message': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const text = extractTextParts(output.parts);
      recordLatestUserMessage(context, {
        at: new Date().toISOString(),
        agent: input.agent || 'leader',
        messageID: input.messageID || null,
        text,
      });
      audit(runtime, { type: 'chat.message', sessionID: input.sessionID, agent: input.agent || 'leader' });
    },

    'tool.execute.before': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
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

      if (features.protectedConfigBlock && ['write', 'edit', 'multiedit'].includes(input.tool)) {
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

      if (['write', 'edit', 'multiedit'].includes(input.tool)) {
        for (const filePath of collectFilePaths(input.args)) {
          recordEditedFile(context, filePath);
        }
      }

      if (input.tool === 'bash') {
        const command = input.args?.command || '';
        const category = classifyVerificationCommand(command);
        if (category) {
          recordVerification(context, category, command, output.title || 'bash');
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
      output.system.push(buildSystemGuard(state));
    },

    'experimental.session.compacting': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const state = loadState(context);
      output.context.push(buildSystemGuard(state));
    },

    'experimental.text.complete': async (input, output) => {
      const context = buildContext(runtime, input.sessionID);
      const triage = parseTriageFromText(output.text);
      if (triage) recordTriage(context, triage);

      const reviewer = parseReviewerFromText(output.text);
      if (reviewer) recordReviewerResult(context, reviewer);

      const manualVerification = parseManualVerificationFromText(output.text);
      if (manualVerification) recordManualVerification(context, manualVerification);

      const verificationFailure = parseVerificationFailureFromText(output.text);
      if (verificationFailure) recordVerificationFailure(context, verificationFailure);

      const features = activeFeatures(runtime, input.sessionID);
      const gateOptions = {
        checkStaleness: features.evidenceStaleness,
        requireAllEvidence: features.requireAllEvidence,
      };

      if (features.closeGate) {
        const current = loadState(context);
        const gatePreview = evaluateCloseGate({
          ...current,
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
