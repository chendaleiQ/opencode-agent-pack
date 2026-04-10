import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

import { projectKey, resolveConfigDir } from './runtime/paths.js';
import { createRuntimeHooks } from './runtime/hook_runtime.js';

const MANAGED_PATHS = ['AGENTS.md', 'agents', 'commands', 'skills', 'tools'];
const PLUGIN_FILE = fileURLToPath(import.meta.url);
const PACKAGE_ROOT = path.resolve(path.dirname(PLUGIN_FILE), '..', '..');

function listSkillNames(skillsRoot) {
  if (!fs.existsSync(skillsRoot)) return [];

  const names = new Set();
  const stack = [skillsRoot];

  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const next = path.join(current, entry.name);
      if (entry.isDirectory()) {
        const skillFile = path.join(next, 'SKILL.md');
        if (fs.existsSync(skillFile)) {
          names.add(path.basename(next));
          continue;
        }
        stack.push(next);
      }
    }
  }

  return [...names].sort();
}

function ensureNoDuplicateSkillSources(repoDir, configDir) {
  const repoSkills = new Set(listSkillNames(path.join(repoDir, 'skills')));
  const externalRoots = [path.join(os.homedir(), '.agents', 'skills')];
  const duplicates = [];

  for (const root of externalRoots) {
    for (const skillName of listSkillNames(root)) {
      if (repoSkills.has(skillName)) {
        duplicates.push({ skillName, root });
      }
    }
  }

  if (duplicates.length === 0) return;

  const duplicateList = duplicates
    .map((item) => `- ${item.skillName} (${item.root})`)
    .join('\n');

  throw new Error(
    [
      'do-the-thing installation stopped because duplicate skill sources were found.',
      'Remove or disable the old skill source before continuing.',
      '',
      'Detected duplicates:',
      duplicateList,
      '',
      `Managed install target: ${path.join(configDir, 'skills')}`,
    ].join('\n'),
  );
}

function syncManagedContent(repoDir, configDir) {
  fs.mkdirSync(configDir, { recursive: true });

  for (const relative of MANAGED_PATHS) {
    const src = path.join(repoDir, relative);
    const dst = path.join(configDir, relative);
    if (!fs.existsSync(src)) continue;
    fs.rmSync(dst, { recursive: true, force: true });
    fs.cpSync(src, dst, { recursive: true });
  }
}

export const DoTheThingPlugin = async ({ project, directory, worktree }) => {
  const configDir = resolveConfigDir();
  ensureNoDuplicateSkillSources(PACKAGE_ROOT, configDir);
  syncManagedContent(PACKAGE_ROOT, configDir);
  const runtimeHooks = createRuntimeHooks({
    configDir,
    projectKey: projectKey({ project, directory, worktree }),
  });

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];

      const installedSkills = path.join(configDir, 'skills');
      if (!config.skills.paths.includes(installedSkills)) {
        config.skills.paths.push(installedSkills);
      }
    },
    ...runtimeHooks,
  };
};
