#!/usr/bin/env python3
"""PreToolUse guard for the Synack test-account e-mail RoE.

Synack requires a self-registered test account address to
  (1) contain "synack", and
  (2) NOT reference any other testing platform.

Both are hard denies. (1) used to be only a warning, which is how an unlabelled
account got created on CRANBERRYBEE - a reportable RoE deviation. (2) used to
match the domain only, so a platform name in the local part slipped through.

Fail-open on malformed input: never break the session.
"""
import json, re, sys

# (2) other-platform references, matched against the WHOLE address (local part + domain).
PLATFORM_TOKENS = [
    "hackerone", "wearehackerone", "bugcrowd", "bugcrowdninja", "intigriti",
    "yeswehack", "ywh", "hackenproof", "immunefi", "cobalt", "zerocopter",
    "inspectiv", "openbugbounty", "huntr", "yogosha", "federacy", "safehats",
    "antihack", "hackrate", "bugv", "bugbounty",
]
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})")

# A real account-creation payload: signup endpoint AND a credential field.
# Deliberately narrow, so merely documenting an address (writing findings.md)
# is not blocked - only a call that actually registers an account.
SIGNUP_EP = re.compile(
    r"viacomAccount/signUp|signUpAndSignIn|/register\b|/signup\b|/sign-up\b|createAccount|"
    r"account/create|users/create|entitledEmail", re.I)
CRED = re.compile(r"[\"']?password[\"']?\s*[:=]|passwd|PasswordSalt", re.I)

def walk(o, out):
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)

def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    chunks = []
    walk(data.get("tool_input", {}), chunks)
    blob = "\n".join(chunks)
    if not blob:
        sys.exit(0)

    addrs = [m.group(0) for m in EMAIL.finditer(blob)]
    if not addrs:
        sys.exit(0)

    bad_platform = sorted({a for a in addrs
                           if any(tok in a.lower() for tok in PLATFORM_TOKENS)})
    if bad_platform:
        deny("BLOCKED by Synack RoE guard: address references another testing platform ("
             + ", ".join(bad_platform) + "). Synack forbids test accounts that reference "
             "another platform - it risks account suspension. Use a neutral mailbox whose "
             "local part contains 'synack'.")

    if SIGNUP_EP.search(blob) and CRED.search(blob):
        unlabelled = sorted({a for a in addrs if "synack" not in a.lower()})
        if unlabelled:
            deny("BLOCKED by Synack RoE guard: account-creation call with an address that "
                 "does not contain 'synack' (" + ", ".join(unlabelled) + "). The target "
                 "briefing requires self-registered accounts to identify as Synack testing.")
    sys.exit(0)

main()
