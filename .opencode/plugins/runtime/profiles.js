export const PROFILES = {
  minimal: {
    auditLogging: true,
    toolCallTracking: true,
    protectedConfigBlock: false,
    noVerifyBlock: false,
    closeGate: false,
    completionRewrite: false,
    evidenceStaleness: false,
    requireAllEvidence: false,
  },
  standard: {
    auditLogging: true,
    toolCallTracking: true,
    protectedConfigBlock: true,
    noVerifyBlock: true,
    closeGate: true,
    completionRewrite: true,
    evidenceStaleness: true,
    requireAllEvidence: false,
  },
  strict: {
    auditLogging: true,
    toolCallTracking: true,
    protectedConfigBlock: true,
    noVerifyBlock: true,
    closeGate: true,
    completionRewrite: true,
    evidenceStaleness: true,
    requireAllEvidence: true,
  },
};

export function profileFromLane(lane) {
  if (lane === 'quick') return 'minimal';
  if (lane === 'standard') return 'standard';
  if (lane === 'guarded' || lane === 'strict') return 'strict';
  return 'standard';
}

export function getProfileFeatures(profileName) {
  return PROFILES[profileName] || PROFILES.standard;
}
