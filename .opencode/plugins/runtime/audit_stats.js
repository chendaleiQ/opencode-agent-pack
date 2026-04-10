import fs from 'fs';

import { auditLogPath } from './paths.js';

export function computeAuditStats({ configDir, projectKey }) {
  const logPath = auditLogPath(configDir, projectKey);
  if (!fs.existsSync(logPath)) {
    return { totalEvents: 0, byType: {}, sessions: [], blockedAttempts: 0 };
  }

  const lines = fs.readFileSync(logPath, 'utf-8').split('\n').filter(Boolean);
  const records = lines
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  const byType = {};
  const sessions = new Set();
  let blockedAttempts = 0;

  for (const record of records) {
    const type = record.type || 'unknown';
    byType[type] = (byType[type] || 0) + 1;
    if (record.sessionID) sessions.add(record.sessionID);
    if (type === 'tool.blocked') blockedAttempts++;
    if (type === 'completion.attempt' && !record.allowed) blockedAttempts++;
  }

  return {
    totalEvents: records.length,
    byType,
    sessions: [...sessions],
    blockedAttempts,
  };
}
