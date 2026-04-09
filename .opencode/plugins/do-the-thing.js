import fs from 'fs';
import os from 'os';
import path from 'path';

const MANAGED_PATHS = ['AGENTS.md', 'agents', 'commands', 'skills', 'tools'];

function resolveConfigDir() {
  const configured = process.env.OPENCODE_CONFIG_DIR?.trim();
  if (configured) return path.resolve(configured);
  return path.join(os.homedir(), '.config', 'opencode');
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

export const DoTheThingPlugin = async ({ directory }) => {
  const configDir = resolveConfigDir();
  syncManagedContent(directory, configDir);

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];

      const installedSkills = path.join(configDir, 'skills');
      if (!config.skills.paths.includes(installedSkills)) {
        config.skills.paths.push(installedSkills);
      }
    },
  };
};
