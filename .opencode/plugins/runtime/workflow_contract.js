import fs from 'fs';

const CONTRACT_PATH = new URL('../../../tools/workflow_contract.json', import.meta.url);
const CONTRACT = JSON.parse(fs.readFileSync(CONTRACT_PATH, 'utf-8'));

export const TRIAGE_REQUIRED_FIELDS = CONTRACT.triage.required_fields;
export const REVIEWER_REQUIRED_FIELDS = CONTRACT.reviewer.required_fields;
export const PLANNING_ARTIFACT_FIELD = CONTRACT.planning.artifact_field;
export const PLANNING_ARTIFACT_KINDS = CONTRACT.planning.artifact_kinds;
export const PLANNING_REQUIRES_QUESTION_TOOL = Boolean(CONTRACT.planning.approval.requires_question_tool);
export const PLANNING_ALLOWS_FREE_TEXT = Boolean(CONTRACT.planning.approval.allows_free_text);

export function hasRequiredFields(candidate, requiredFields) {
  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return false;
  return requiredFields.every((field) => {
    const value = candidate[field];
    return value !== null && value !== undefined && value !== '';
  });
}
