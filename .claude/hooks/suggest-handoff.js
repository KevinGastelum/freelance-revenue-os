#!/usr/bin/env node
/*
 * Checkpoint nudge (PostToolUse:Bash). When a phase merges to `main` AND the
 * session is long (tool-calls since last checkpoint >= threshold), suggest
 * running /session-close-wr then /clear. Token-count isn't available in hooks,
 * so tool-call count is the proxy. FAIL OPEN: any error => exit 0.
 */
'use strict';
const fs = require('fs');
const path = require('path');
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', function (c) { raw += c; });
process.stdin.on('error', function () { process.exit(0); });
process.stdin.on('end', function () { try { main(raw); } catch (_) { process.exit(0); } });
function main(input) {
  const data = JSON.parse(input || '{}');
  if ((data.hook_event_name || data.hookEventName) !== 'PostToolUse') process.exit(0);
  const ti = data.tool_input || data.toolInput || {};
  const cmd = (ti.command || '').toString();
  const THRESH = parseInt(process.env.WR_HANDOFF_THRESHOLD || '40', 10);
  const dir = process.env.TEMP || process.env.TMP || process.env.TMPDIR || '/tmp';
  const stateFile = path.join(dir, 'wr-handoff-counter.json');
  let st = { n: 0 };
  try { st = JSON.parse(fs.readFileSync(stateFile, 'utf8')); } catch (_) {}
  st.n = (st.n || 0) + 1;
  const isMerge = /\/pulls\/\d+\/merge|merge\s+--ff-only\s+origin\/main/i.test(cmd);
  let msg = '';
  if (isMerge && st.n >= THRESH) {
    msg = '\n[checkpoint] A phase merged to main and this session is long (' + st.n +
      ' tool calls since last checkpoint).\nConsider: /session-close-wr -> /clear -> /session-start-wr to avoid context bloat/drift.\n';
    st.n = 0;
  }
  try { fs.writeFileSync(stateFile, JSON.stringify(st)); } catch (_) {}
  if (msg) process.stdout.write(msg);
  process.exit(0);
}
