// Read-only repository inventory and redacted secret heuristics. Never stages files.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const output = path.join(os.tmpdir(), 'aqlith-cairo-qa');
fs.mkdirSync(output, { recursive: true });
const git = args => execFileSync('git', args, { cwd: root, encoding: 'utf8' });
const status = git(['status', '--porcelain=v1', '--untracked-files=all']);
const manual = new Set(['apps/tutor-web/AGENTS.md', 'apps/tutor-web/CLAUDE.md', 'apps/tutor-web/next-env.d.ts', 'tools/qa/migrate_mobile_styles.py']);
const findings = [];
const inventory = status.trimEnd().split(/\r?\n/).filter(Boolean).map(row => {
  const file = row.slice(3);
  const binary = /\.(png|ttf)$/.test(file);
  const category = manual.has(file) ? 'manual review; exclude from staging' : /assets\/brand|public\/brand/.test(file) ? 'approved original logo' : /fonts\/cairo|FONT-LICENSES/.test(file) ? 'licensed bundled font/license' : file.startsWith('tools/qa/') ? 'QA source' : /package(-lock)?\.json$/.test(file) ? 'dependency manifest/lockfile' : 'application source/config/documentation';
  if (!binary) {
    const lines = fs.readFileSync(path.join(root, file), 'utf8').split(/\r?\n/);
    const rules = [
      ['private key', /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/],
      ['provider key', /(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{24,}|AccountKey=[A-Za-z0-9+/=]{32,})/],
      ['embedded JWT', /eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}/],
      ['literal credential', /(?:password|secret_key|api_key|access_token)\s*[:=]\s*["'][A-Za-z0-9_+\/-]{24,}["']/i],
    ];
    lines.forEach((line, index) => rules.forEach(([rule, pattern]) => { if (pattern.test(line)) findings.push({ file, line: index + 1, rule }); }));
  }
  return { status: row.slice(0, 2), file, category, bytes: fs.statSync(path.join(root, file)).size };
});
const allowlist = inventory.filter(item => !manual.has(item.file)).map(item => item.file);
const fontHashes = inventory.filter(item => item.file.endsWith('.ttf')).map(item => ({ file: item.file, sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, item.file))).digest('hex') }));
const ignored = git(['status', '--short', '--ignored']).split(/\r?\n/).filter(line => line.startsWith('!! ')).map(line => line.slice(3));
const report = {
  branch: git(['branch', '--show-current']).trim(), head: git(['rev-parse', 'HEAD']).trim(),
  stagedFiles: git(['diff', '--cached', '--name-only']).trim().split(/\r?\n/).filter(Boolean),
  inventory, allowlist, manualReview: [...manual], redactedSecretFindings: findings,
  secretScanScope: 'Full text of all modified/untracked nonbinary files; heuristic only, never includes matched values.',
  fontHashes, ignoredArtifacts: ignored,
  excludeFromCheckpoint: ['AGENTS.md/CLAUDE.md generated instructions', 'next-env.d.ts generated dev references', 'one-time style migration helper', 'node_modules/.next/.expo caches and tsbuildinfo', '.env files', 'temporary preview account credentials', 'temporary databases', 'screenshots containing test records'],
};
fs.writeFileSync(path.join(output, 'checkpoint-inventory.json'), JSON.stringify(report, null, 2));
fs.writeFileSync(path.join(output, 'staging-allowlist.txt'), allowlist.join('\n') + '\n');
fs.writeFileSync(path.join(output, 'git-status.txt'), status);
console.log(JSON.stringify({ modified: inventory.filter(item => item.status === ' M').length, untracked: inventory.filter(item => item.status === '??').length, recommendedPaths: allowlist.length, staged: report.stagedFiles.length, secretFindings: findings, manualReview: report.manualReview, ignoredArtifactGroups: ignored.length }, null, 2));
