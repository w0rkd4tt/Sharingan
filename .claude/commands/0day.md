---
description: "Patch-first 0-day vulnerability research pipeline"
---

﻿---
description: "Patch-first 0-day vulnerability research pipeline"
---

# /0day — Patch-First 0-Day Research

Hunt for 0-days in software products using patch-first methodology: analyze ALL security patches first, then find vulnerable versions and hunt in old code.

> **Note:** `/hunt-variant --0day <repo>` provides the same patch-first workflow with additional CVE variant analysis. Use `/0day` for standalone 0-day research; use `/hunt-variant` when starting from a known CVE or tech stack.

## Usage
```
/0day https://github.com/ORG/REPO      # Clone and analyze
/0day /path/to/local/repo               # Analyze local repo
/0day nginx                             # Search by product name
/0day [target] --deep                   # Exhaustive: KHÔNG skip bất kỳ patch nào
```

## 7-Step Workflow (MANDATORY ORDER)

### Step 1: Collect ALL Security Patches (KHÔNG SKIP)

```bash
cd targets/_temp/repos/REPO

# Git log with security keywords
git log --oneline --all --grep="security" --grep="CVE" --grep="fix" --grep="vuln" --grep="patch" --grep="sanitize" --grep="escape" --grep="inject" -i > security_commits.txt

# Or use variant_hunter
python tools/variant_hunter.py patches /path/to/repo
```

### Step 2: Diff ALL Patches (MANDATORY)

```bash
# Diff specific commit
python tools/variant_hunter.py diff /path/to/repo COMMIT_HASH

# Hoặc manual
git show COMMIT_HASH --stat
git show COMMIT_HASH
```

**Phân tích mỗi patch cho:**
- File changed: route handler? util? middleware? core?
- What was added: validation? sanitization? auth check? blocklist?
- What was the bug: missing check? improper encoding? logic flaw?
- Attack vector: user input? header? query param? body? file upload?

### Step 3: Find Vulnerable Versions

```bash
python tools/variant_hunter.py vulnver /path/to/repo --patch COMMIT_HASH

# Manual: list tags sorted by date
git tag --sort=-creatordate | head -30

# Check if patch present in tag
git merge-base --is-ancestor PATCH_COMMIT TAG && echo "patched" || echo "VULNERABLE"
```

**Rule**: Focus 1-2 releases TRƯỚC bản patch = highest vulnerability probability.

### Step 4: Deep Dive — Hunt 0-Day (TRUE 0-DAY)

**TRUE 0-DAY = Find SAME vulnerability pattern in UNFIXED code locations.**
**N-DAY = Find targets running OLD vulnerable versions (Step 5).**

```bash
# Checkout vulnerable version
git checkout v2.4.0

# Same sink, different file
grep -rn "innerHTML\|document.write\|eval(" --include="*.js" .

# SQLi patterns
grep -rn "execute(\|query(\|raw(" --include="*.py" --include="*.js" .

# Command injection
grep -rn "exec(\|spawn(\|system(\|popen(" .

# SSRF
grep -rn "request(\|fetch(\|urllib\|http\.get" .
```

### Step 4.5: Pattern Extraction & Codebase-Wide Search (TRUE 0-DAY)

**Core idea**: Patch fixes ONE location. Extract the VULNERABLE PATTERN, then grep ENTIRE codebase.

```bash
# 1. From patch diff, identify the VULNERABLE PATTERN
# Example: patch added `sanitize(input)` before `db.query(input)`
# Vulnerable pattern = `db.query(` WITHOUT preceding `sanitize(`

# 2. Grep for ALL occurrences of the SINK without the FIX
grep -rn "db\.query(" . | grep -v "sanitize" > potential_vulns.txt

# 3. For each hit, check if input is user-controlled
# Manual review or LLM-assisted taint analysis

# 4. Check if hit is in DIFFERENT code path than patched one
# Same file, different function? Different file entirely?
```

**Pattern extraction examples:**

| Patch Type | Vulnerable Pattern | Grep Command |
|------------|-------------------|--------------|
| XSS sanitization | `.innerHTML = userInput` | `grep -rn "\.innerHTML\s*=" \| grep -v "sanitize\|escape\|encode"` |
| SQLi parameterization | `query("SELECT..."+input)` | `grep -rn "query.*\+\|execute.*%s" --include="*.py"` |
| Command injection | `exec(cmd + userInput)` | `grep -rn "exec(\|system(\|popen(" \| grep -v "shlex\|escape"` |
| Path traversal | `open(basePath + userInput)` | `grep -rn "open(\|readFile(" \| grep -v "normalize\|resolve"` |
| Auth bypass | Missing `if (isAuthenticated)` | `grep -rn "@route\|app\.get\|app\.post" \| grep -v "auth\|login_required"` |

**LLM-assisted pattern extraction:**
```
PROMPT: Given this patch diff:
[PASTE DIFF]

1. What is the VULNERABLE PATTERN that was fixed?
2. Generate a grep command to find ALL OTHER occurrences of this pattern
3. What variations of this pattern might exist (different function names, different syntax)?
```

### Step 5: Shodan/ZoomEye — Find Real Targets

```bash
# Shodan search with scope filtering
python tools/variant_hunter.py shodan "product:nginx version:1.18"

# ZoomEye search
python tools/variant_hunter.py zoomeye "app:nginx +ver:1.18"

# Or use uncover (multi-engine)
uncover -q "nginx 1.18" -e shodan,zoomeye,fofa -silent | tee targets_raw.txt

# Filter against bug bounty scope
python tools/variant_hunter.py scope-filter targets_raw.txt -o inscope.txt
```

### Step 6: POC Validation

```bash
python tools/variant_hunter.py poc https://target.com/vuln --vuln-type xss

# Vuln types: xss, sqli, ssrf, path_traversal, auth_bypass
```

**POC Evidence Checklist:**
- [ ] Target URL/IP in scope
- [ ] Version confirmed vulnerable
- [ ] Raw HTTP request/response captured
- [ ] Screenshot of exploitation
- [ ] Impact demonstrated
- [ ] Reproduction steps documented

### Step 7: False Positive Handling

```bash
# If POC fails → mark as false positive
python tools/variant_hunter.py fp-cleanup FINDING-NNN --reason version_mismatch

# List pending findings
python tools/variant_hunter.py fp-list

# Show paths for quick verification
python tools/variant_hunter.py paths FINDING-NNN

# Dry run first
python tools/variant_hunter.py fp-cleanup FINDING-NNN --reason waf_blocked --dry-run

# Batch cleanup
python tools/variant_hunter.py fp-cleanup FINDING-042 FINDING-043 --reason version_mismatch
```

**FP Reasons:**
| Reason | Khi nào |
|--------|---------|
| `version_mismatch` | Target đã patched |
| `waf_blocked` | WAF blocks payload |
| `not_exploitable` | Misconfig nhưng không exploit được |
| `out_of_scope` | Target ngoài scope |
| `duplicate` | Đã có finding khác |
| `intended_behavior` | By design |
| `poc_failed` | POC fail sau 3 lần |

## Search Query Patterns

### Shodan
```
product:nginx version:1.18
http.title:"WordPress" http.html:"ver=5.8"
http.component:"spring" http.html:"2.5.0"
product:mongodb version:4.2
http.html:"X-Powered-By: CustomApp/1.0"
```

### ZoomEye
```
app:nginx +ver:1.18
app:wordpress +ver:5.8
app:spring +ver:2.5.0
banner:"Server: CustomApp/1.0"
```

## Output Structure

```
targets/_temp/0day-analysis/{repo-name}/
├── 0day-patches-{repo-name}.json    # Patch analysis (structured)
├── 0day-diff-{commit_short}.md      # Diff analysis per commit
├── 0day-vulnver-{repo-name}.json    # Vulnerable versions
├── 0day-similar-patterns-{commit_short}.md  # Deepgrep results
└── {repo-name}_patches.md           # Patch summary
targets/_temp/repos/
└── {repo-name}/                     # Cloned repo (gitignored)
```

## Rules
- **PATCH-FIRST**: KHÔNG deep dive trước khi diff TẤT CẢ security patches
- **VERSION CHECK**: Xác định version vulnerable TRƯỚC khi test
- **1-2 RELEASE BACK**: Focus versions ngay trước patch
- **SAME CLASS, DIFFERENT FILE**: Grep cùng pattern ở file khác
- **SCOPE CHECK**: `/scope-check` trước khi test any target
- **CLEANUP FP**: Luôn cleanup false positives để giữ findings clean

---

## Audit Priority: New/Unreviewed Code (HIGH ROI)

**Core insight**: New code paths have LESS security review. CVEs cluster in recently added features.

### High-Priority Code Areas

| Pattern | Why High Priority | Grep |
|---------|------------------|------|
| New protocols (HTTP/3, QUIC, WebTransport) | Complex, less tested | `vquic/*.c`, `ws.c`, `mqtt.c` |
| Async/concurrent code | Race conditions | `async`, `await`, `Promise`, `thread`, `mutex` |
| Parser code | Memory bugs, injection | `parse`, `decode`, `deserialize` |
| File handling | Path traversal, symlink | `fopen`, `readFile`, `writeFile` |
| Crypto implementations | Timing attacks, weak random | `encrypt`, `decrypt`, `hash`, `random` |
| Error handling | Information disclosure | `catch`, `except`, `error`, `debug` |
| Config loading | Injection, SSRF | `config`, `settings`, `env`, `yaml`, `json` |

### Finding New/Unreviewed Code

```bash
# 1. Recently added files (last 6 months)
git log --since="6 months ago" --name-only --pretty=format: | sort -u | grep -E "\.(c|js|py|java)$"

# 2. Files with few commits (less review)
for f in $(find . -name "*.c" -o -name "*.js"); do
  commits=$(git log --oneline "$f" 2>/dev/null | wc -l)
  if [ "$commits" -lt 5 ]; then echo "$f: $commits commits"; fi
done | sort -t: -k2 -n

# 3. Files never mentioned in security commits
git log --all --grep="security\|CVE\|fix" --name-only --pretty=format: | sort -u > security_touched.txt
find . -name "*.c" | while read f; do
  grep -q "$f" security_touched.txt || echo "NEVER AUDITED: $f"
done

# 4. Experimental/beta features
grep -rn "experimental\|beta\|TODO\|FIXME\|XXX\|HACK" --include="*.c" --include="*.js"
```

### Audit Checklist for New Code

```markdown
## New Code Audit: [FILE/FEATURE]
- [ ] Added within last 6 months?
- [ ] < 5 commits (low review)?
- [ ] Complex protocol/parser?
- [ ] Handles user input?
- [ ] Has async/concurrent logic?
- [ ] Missing from security commit history?
```

---

## Logic & Race Condition Patterns (NEVER HAD CVE)

**Core insight**: Some bug classes rarely get CVEs but are highly exploitable.

### Logic Bug Patterns

```bash
# 1. State machine inconsistencies
grep -rn "state\s*=\|status\s*=" . | grep -v "const\|readonly"

# 2. Privilege checks with gaps
grep -rn "isAdmin\|hasPermission\|canAccess" . 
# Then verify: is check present on ALL paths to sensitive operation?

# 3. Resource limits without enforcement
grep -rn "limit\|max\|quota" . | grep -v "enforce\|check\|validate"

# 4. Business logic (pricing, credits, subscriptions)
grep -rn "price\|cost\|credit\|balance\|subscription" .

# 5. Multi-step flows (checkout, registration)
# Map all steps → verify: can any step be skipped? repeated? reordered?
```

### Race Condition Patterns

```bash
# 1. Check-then-act (TOCTOU)
# Pattern: if (check) { act } — race window between check and act
grep -rn "if.*exists\|if.*canAccess" -A5 . | grep -E "open\|read\|write\|delete"

# 2. Double-fetch vulnerabilities
# Pattern: read(x) ... validate(x) ... use(read(x)) — second read may differ
grep -rn "req\.body\|request\.json\|params\[" . 
# Check if same value fetched multiple times

# 3. Counter/balance races
grep -rn "\+\+\|--\|\+=\|-=" . | grep -i "count\|balance\|credit"

# 4. Lock-free concurrent access
grep -rn "global\|shared\|static" . | grep -v "mutex\|lock\|synchronized"
```

### Testing Race Conditions

```bash
# 1. Burp Intruder with Pitchfork
# Set same request 10x with null payload → look for inconsistent responses

# 2. turbo-intruder (Burp extension)
# Use race.py template for single-packet attack

# 3. Manual parallel curl
for i in {1..10}; do
  curl -X POST "TARGET/api/transfer" -d "amount=100" &
done
wait
# Check if 10 requests = 10x deduction or only 1x

# 4. Playwright parallel
await Promise.all([
  page1.click('#submit'),
  page2.click('#submit'),
  page3.click('#submit')
]);
```

### Logic Bug Audit Template

```markdown
## Logic Audit: [FEATURE]

### State Analysis
- States: [list all states]
- Transitions: [which transitions are valid?]
- FINDING: Can reach state X without going through state Y?

### Permission Analysis
- Protected resources: [list]
- Check locations: [where are permissions checked?]
- FINDING: Any path to resource without check?

### Flow Analysis
- Steps: [1, 2, 3, ...]
- Dependencies: [which steps depend on which?]
- FINDING: Can skip step N? Repeat step N? Reorder?

### Race Window Analysis
- Critical section: [code between check and act]
- Window size: [estimated time in ms]
- FINDING: Can parallel requests exploit window?
```
