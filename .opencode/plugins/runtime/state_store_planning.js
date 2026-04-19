export function createPlanningGate(enabled = false) {
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

export function deriveBlockedStage(planningGate) {
  if (!planningGate?.enabled) return null;
  if (planningGate.specStatus !== 'approved') return 'spec';
  if (planningGate.planStatus !== 'approved') return 'plan';
  return null;
}

export function normalizePlanningGate(planningGate, needsPlan = false) {
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

export function summarizeQuestions(questions = []) {
  return questions.map((question) => ({
    header: question?.header || '',
    question: question?.question || '',
    options: Array.isArray(question?.options)
      ? question.options.map((option) => option?.label || '').filter(Boolean)
      : [],
  }));
}

export function removePendingQuestion(pendingQuestions = [], requestID) {
  if (!requestID) return pendingQuestions;
  return pendingQuestions.filter((item) => item?.requestID !== requestID);
}
