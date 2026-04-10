import fs from 'fs';

import { auditLogPath } from './paths.js';

export function appendAuditRecord({ configDir, projectKey }, record) {
  const line = JSON.stringify({ at: new Date().toISOString(), ...record });
  fs.appendFileSync(auditLogPath(configDir, projectKey), `${line}\n`, 'utf-8');
}
