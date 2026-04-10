const PROTECTED_CONFIG_PATTERNS = [
  /(^|\/)eslint\.config\.(js|cjs|mjs)$/i,
  /(^|\/)\.eslintrc(\.(js|cjs|json|yaml|yml))?$/i,
  /(^|\/)biome\.json(c)?$/i,
  /(^|\/)prettier\.config\.(js|cjs|mjs)$/i,
  /(^|\/)\.prettierrc(\.(js|cjs|json|yaml|yml))?$/i,
  /(^|\/)ruff\.toml$/i,
  /(^|\/)\.markdownlint(\.json)?$/i,
];

function extractJsonCandidates(text) {
  const candidates = [];
  const fenced = text.matchAll(/```json\s*([\s\S]*?)```/gi);
  for (const match of fenced) candidates.push(match[1]);
  const bare = text.match(/\{[\s\S]*\}/);
  if (bare) candidates.push(bare[0]);
  return candidates;
}

function tryParseObject(text) {
  for (const candidate of extractJsonCandidates(text)) {
    try {
      const parsed = JSON.parse(candidate);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
    } catch {
      // ignore parse failure
    }
  }
  return null;
}

export function parseTriageFromText(text) {
  const parsed = tryParseObject(text);
  if (!parsed) return null;
  if (!parsed.lane || !parsed.complexity || !parsed.risk || !parsed.finalApprovalTier) return null;
  return parsed;
}

export function parseReviewerFromText(text) {
  const parsed = tryParseObject(text);
  if (!parsed) return null;
  if (!parsed.specCompliance || !parsed.codeQuality) return null;
  return parsed;
}

export function isProtectedConfigPath(filePath) {
  if (!filePath) return false;
  return PROTECTED_CONFIG_PATTERNS.some((pattern) => pattern.test(filePath));
}

export function isNoVerifyCommand(command) {
  return /git\s+commit\b/.test(command) && /--no-verify\b/.test(command);
}

export function classifyVerificationCommand(command) {
  if (!command) return null;
  const normalized = command.toLowerCase();
  if (/(^|\s)(npm|pnpm|yarn|bun)\s+test\b|pytest\b|cargo\s+test\b|go\s+test\b/.test(normalized)) return 'tests';
  if (/(^|\s)(npm|pnpm|yarn|bun)\s+run\s+lint\b|ruff\s+check\b|eslint\b|biome\s+check\b/.test(normalized)) return 'lint';
  if (/tsc\b|pyright\b|mypy\b|cargo\s+check\b/.test(normalized)) return 'typecheck';
  if (/(^|\s)(npm|pnpm|yarn|bun)\s+run\s+build\b|vite\s+build\b|next\s+build\b/.test(normalized)) return 'build';
  return null;
}

function evidenceList(state, key) {
  const items = state?.evidence?.[key];
  return Array.isArray(items) ? items : [];
}

export function resolveEvidenceRequirements(state) {
  const requirements = ['triage'];
  if ((state?.editedFiles || []).length > 0) requirements.push('verification-or-manual');
  if (state?.triage?.needsReviewer) requirements.push('review');
  return requirements;
}

export function resolveMissingEvidence(state) {
  const missing = [];
  const requirements = resolveEvidenceRequirements(state);
  const triageEvidence = evidenceList(state, 'triage');
  const reviewEvidence = evidenceList(state, 'review');
  const verificationEvidence = evidenceList(state, 'verification');
  const manualEvidence = evidenceList(state, 'manual');

  if (requirements.includes('triage') && triageEvidence.length === 0) {
    missing.push('missing triage evidence');
  }

  if (requirements.includes('review')) {
    const hasPassingReview = reviewEvidence.some((item) => item?.status === 'passed');
    if (!hasPassingReview) missing.push('missing review evidence');
  }

  if (requirements.includes('verification-or-manual')) {
    const hasPassingVerification = verificationEvidence.some((item) => item?.status === 'passed');
    const hasPassingManual = manualEvidence.some((item) => item?.status === 'passed');
    if (!hasPassingVerification && !hasPassingManual) {
      missing.push('missing verification evidence');
    }
  }

  return missing;
}

export function evaluateCloseGate(state) {
  const missing = [];
  if (state?.phase !== 'closable') missing.push('state not closable');
  if (!state?.triage) missing.push('missing triage');
  missing.push(...resolveMissingEvidence(state));
  if ((state?.editedFiles || []).length > 0) {
    const verificationStatus = state?.verification?.status;
    if (!['passed', 'manual_passed'].includes(verificationStatus)) {
      missing.push(
        verificationStatus === 'failed'
          ? 'failed verification'
          : verificationStatus === 'pending'
            ? 'verification still pending'
            : 'missing verification evidence',
      );
    }
  }
  if (state?.triage?.needsReviewer && state?.reviewer?.status !== 'passed') {
    missing.push('missing reviewer pass');
  }
  return {
    allowed: missing.length === 0,
    missing: [...new Set(missing)],
  };
}

export function buildSystemGuard(state) {
  const gate = evaluateCloseGate(state);
  const triage = state?.triage;
  const verificationStatus = state?.verification?.status || 'missing';
  const phase = state?.phase || 'unknown';
  const entryType = state?.entryType || 'general';
  const lines = [
    'do-the-thing runtime guard:',
    '- You must not claim completion or closure unless the close gate is satisfied.',
    '- If evidence is missing, explicitly continue with verification or review instead of closing.',
  ];
  if (triage) {
    lines.push(`- Active lane: ${triage.lane}; complexity=${triage.complexity}; risk=${triage.risk}.`);
  } else {
    lines.push('- No recorded triage yet. Do not act as if workflow routing is complete.');
  }
  lines.push(`- Entry type: ${entryType}; phase: ${phase}.`);
  lines.push(`- Verification status: ${verificationStatus}.`);
  if (!gate.allowed) {
    lines.push(`- Close gate currently blocked by: ${gate.missing.join(', ')}.`);
  }
  return lines.join('\n');
}

export function detectClosureAttempt(text) {
  if (!text) return false;
  return /(changeSummary\s*:|closeReason\b|\b(quick|standard|guarded|strict)\s*\|\s*(low|high)\s*\|\s*(low|high)\b|任务完成|已完成|completed successfully|work is complete)/i.test(text);
}

export function buildBlockedCompletionMessage(state, missing) {
  const triageLane = state?.triage?.lane ? `lane=${state.triage.lane}` : 'lane=unknown';
  const editedCount = (state?.editedFiles || []).length;
  const verificationStatus = state?.verification?.status || 'missing';
  const phase = state?.phase || 'unknown';
  const entryType = state?.entryType || 'general';
  return [
    'Completion blocked by do-the-thing runtime.',
    `Current workflow state: ${triageLane}, entryType=${entryType}, phase=${phase}, editedFiles=${editedCount}, verification=${verificationStatus}.`,
    'Missing close-gate evidence:',
    ...missing.map((item) => `- ${item}`),
    '',
    'Do not close yet. Continue with the missing review/verification steps and then try again.',
  ].join('\n');
}

export function extractTextParts(parts = []) {
  return parts
    .map((part) => {
      if (typeof part?.text === 'string') return part.text;
      if (typeof part?.content === 'string') return part.content;
      if (typeof part?.message === 'string') return part.message;
      return '';
    })
    .filter(Boolean)
    .join('\n');
}

export function parseManualVerificationFromText(text) {
  if (!text) return null;
  if (/(manual (check|verification)|手动(检查|验证)|manually checked)/i.test(text)) {
    return text.slice(0, 500);
  }
  return null;
}

export function parseVerificationFailureFromText(text) {
  if (!text) return null;
  if (/(verification failed|tests failed|lint failed|typecheck failed|build failed|验证失败|测试失败|类型检查失败)/i.test(text)) {
    return text.slice(0, 500);
  }
  return null;
}

export function collectFilePaths(args) {
  if (!args || typeof args !== 'object') return [];
  const values = [];
  for (const [key, value] of Object.entries(args)) {
    if (/file(path)?/i.test(key) && typeof value === 'string') values.push(value);
    if (Array.isArray(value)) {
      for (const item of value) {
        if (typeof item === 'string' && /\//.test(item)) values.push(item);
        if (item && typeof item === 'object') values.push(...collectFilePaths(item));
      }
    }
    if (value && typeof value === 'object') values.push(...collectFilePaths(value));
  }
  return [...new Set(values)];
}
