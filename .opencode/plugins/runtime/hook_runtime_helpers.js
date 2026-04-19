import {
  hasValidTriage,
  loadState,
  recordEscalationEvidence,
} from './state_store.js';

const LANE_ORDER = ['quick', 'standard', 'guarded', 'strict'];

export function isAllowedPreTriageTool(toolName, args) {
  if (['glob', 'grep', 'read'].includes(toolName)) return true;
  if (toolName !== 'skill') return false;
  return ['using-superpowers', 'dtt-change-triage'].includes(args?.name);
}

export function isLeaderManagedSession(state) {
  const agent = state?.latestUserMessage?.agent || null;
  return !agent || agent === 'leader';
}

export function planningArtifactKindForPath(filePath) {
  if (!filePath) return null;
  const normalized = String(filePath).replaceAll('\\', '/');
  if (/(^|\/)docs\/dtt\/specs\/[^/]+\.md$/i.test(normalized)) return 'spec';
  if (/(^|\/)docs\/dtt\/plans\/[^/]+\.md$/i.test(normalized)) return 'plan';
  return null;
}

export function isFileMutationTool(toolName) {
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

export function isPlanningDecisionQuestion(args, blockedStage) {
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

export function classifyPlanningQuestionDecision(answers = [], rejected = false) {
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

export function enforceTriageBeforeExecution({ buildContext, audit }, runtime, sessionID, kind, name, args) {
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

function laneRank(lane) {
  const index = LANE_ORDER.indexOf(lane);
  return index >= 0 ? index : -1;
}

export function maybeRecordReviewerEscalation(context, reviewer) {
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

export function childSessionIDFromOutput(output) {
  return output?.metadata?.sessionID || output?.metadata?.sessionId || output?.sessionID || output?.sessionId || null;
}
