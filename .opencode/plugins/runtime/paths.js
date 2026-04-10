import crypto from 'crypto';
import fs from 'fs';
import os from 'os';
import path from 'path';

export function resolveConfigDir() {
  const configured = process.env.OPENCODE_CONFIG_DIR?.trim();
  if (configured) return path.resolve(configured);
  return path.join(os.homedir(), '.config', 'opencode');
}

export function runtimeRoot(configDir) {
  return path.join(configDir, 'do-the-thing');
}

export function sessionsRoot(configDir) {
  return path.join(runtimeRoot(configDir), 'sessions');
}

export function auditRoot(configDir) {
  return path.join(runtimeRoot(configDir), 'audit');
}

export function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
  return dirPath;
}

function safeSlug(value) {
  return String(value || 'project')
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40) || 'project';
}

export function projectKey({ project, directory, worktree }) {
  const basis = project?.id || project?.root || worktree || directory || 'unknown-project';
  const hash = crypto.createHash('sha256').update(String(basis)).digest('hex').slice(0, 12);
  const label = safeSlug(path.basename(String(directory || worktree || basis)));
  return `${label}-${hash}`;
}

function safeSessionID(sessionID) {
  return String(sessionID || 'session').replace(/[^a-zA-Z0-9._-]+/g, '-');
}

export function sessionStatePath(configDir, projectKeyValue, sessionID) {
  const dir = ensureDir(path.join(sessionsRoot(configDir), projectKeyValue));
  return path.join(dir, `${safeSessionID(sessionID)}.json`);
}

export function latestStatePath(configDir, projectKeyValue) {
  const dir = ensureDir(path.join(sessionsRoot(configDir), projectKeyValue));
  return path.join(dir, 'latest.json');
}

export function auditLogPath(configDir, projectKeyValue) {
  const dir = ensureDir(path.join(auditRoot(configDir), projectKeyValue));
  return path.join(dir, 'audit.jsonl');
}
