#!/usr/bin/env node
/*
 * Warren safety guard for Claude Code hooks (freelance-revenue-os).
 *
 * Wired in .claude/settings.json for SessionStart + PreToolUse (Bash|PowerShell).
 * Defense-in-depth against leaking WARREN_API_TOKEN / .env contents and against
 * destructive Warren project deletes dispatched from an agent shell.
 *
 * CONTRACT: FAIL OPEN. Any parse/logic error => exit 0 (allow). This is a safety
 * net, not a sandbox; the real protections are agent instructions + human review.
 * It must never wedge legitimate work (e.g. curl with an Authorization: Bearer
 * header is allowed; only *printing* the token is blocked).
 *
 * Block protocol: exit code 2 + reason on stderr => Claude Code blocks the call.
 */
'use strict';

let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', function (c) { raw += c; });
process.stdin.on('error', function () { process.exit(0); });
process.stdin.on('end', function () {
  try { main(raw); } catch (_) { process.exit(0); }
});

function main(input) {
  let data;
  try { data = JSON.parse(input || '{}'); } catch (_) { process.exit(0); return; }

  const event = data.hook_event_name || data.hookEventName || '';

  if (event === 'SessionStart') {
    process.stdout.write(
      '[Warren] This repo is Warren-aware. Health: scripts/wr-health.sh | ' +
      'Projects: scripts/wr-projects.sh. Never print WARREN_API_TOKEN or .env ' +
      'contents; never auto-merge Warren branches. See CLAUDE.md.\n'
    );
    process.exit(0);
  }

  if (event !== 'PreToolUse') process.exit(0);

  const ti = data.tool_input || data.toolInput || {};
  const cmd = (ti.command || '').toString();
  if (!cmd) process.exit(0);

  const reason = firstViolation(cmd);
  if (reason) {
    process.stderr.write(
      'Blocked by Warren safety policy: ' + reason + '.\n' +
      'If this is legitimate, run it yourself or adjust ' +
      '.claude/hooks/warren-guard.js.\n'
    );
    process.exit(2);
  }
  process.exit(0);
}

function firstViolation(cmd) {
  // Reference to the token var in bash ($TOK / ${TOK}) or PowerShell ($env:TOK).
  const TOKEN = /\$\{?(?:env:)?WARREN_API_TOKEN/i;
  // Shell verbs that write to stdout/a file.
  const PRINT = /\b(echo|printf|write-output|write-host|out-host|out-default)\b/i;

  // 1. Printing the token.
  if (PRINT.test(cmd) && TOKEN.test(cmd))
    return 'prints WARREN_API_TOKEN to output';
  if (/\bprintenv\s+WARREN_API_TOKEN\b/i.test(cmd))
    return 'prints WARREN_API_TOKEN via printenv';
  if (/(^|[\n;&|])\s*\$env:WARREN_API_TOKEN\s*([\n;&|>]|$)/i.test(cmd))
    return 'evaluates $env:WARREN_API_TOKEN as a bare command (would print it)';

  // 2. Dumping the whole environment (includes the token).
  if (/(^|[\n;|&])\s*(printenv|env)\s*(\||$)/i.test(cmd))
    return 'dumps the full environment (includes WARREN_API_TOKEN)';
  if (/\b(get-childitem|gci|ls|dir|get-item)\s+env:(\\|\s|$|WARREN)/i.test(cmd))
    return 'lists the PowerShell env: drive (includes WARREN_API_TOKEN)';

  // 3. Reading a secret .env (but allow .env.example/.sample/.template).
  if (/\b(cat|less|more|head|tail|nl|bat|strings|xxd|od|type|gc|get-content|get-item|gi)\b[^|&;\n]*\.env\b(?!\.(?:example|sample|template))/i.test(cmd))
    return 'reads a secret .env file';

  // 4. Deleting a Warren project (destructive; any argument order).
  const isHttp = /\b(curl|wget|invoke-restmethod|invoke-webrequest|iwr|irm)\b/i.test(cmd);
  const hitsProjects = /\/projects\//i.test(cmd);
  const isDelete = /(-x\s*delete|-method\s+delete|(^|\s)delete\s+https?:)/i.test(cmd);
  if (isHttp && hitsProjects && isDelete)
    return 'deletes a Warren project (destructive)';

  return null;
}
