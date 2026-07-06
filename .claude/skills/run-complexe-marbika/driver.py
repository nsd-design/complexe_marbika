#!/usr/bin/env python
"""
Smoke driver for the Complexe Marbika Django app.

Drives the ACTUAL running server over HTTP (stdlib only, no pip deps):
  1. waits for the server to be reachable
  2. asserts an unauthenticated page redirects to /login/
  3. logs in through the real CSRF-protected login form
  4. fetches a login-required page and asserts it renders
  5. hits the DRF attendance API and asserts it returns JSON

Prereq: the server must be running (see SKILL.md) and a login user must
exist. Defaults match the `smoke_test` user documented in SKILL.md.

Usage:
    python driver.py [--base URL] [--user U] [--password P]
Env fallbacks: SMOKE_BASE, SMOKE_USER, SMOKE_PASS

Exit code 0 = all checks passed, 1 = a check failed.
"""
import argparse
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CSRF_INPUT = re.compile(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"')


def build_opener():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    # Don't auto-follow redirects: we assert on 302s explicitly.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener2 = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), NoRedirect
    )
    return opener, opener2, jar


def get(opener, url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        resp = opener.open(req, timeout=15)
        return resp.getcode(), resp.read().decode("utf-8", "replace"), resp
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e


def wait_ready(base, tries=30):
    for i in range(tries):
        try:
            urllib.request.urlopen(base + "/login/", timeout=3)
            return True
        except urllib.error.HTTPError:
            return True  # any HTTP response means it's up
        except Exception:
            time.sleep(1)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("SMOKE_BASE", "http://127.0.0.1:8000"))
    ap.add_argument("--user", default=os.environ.get("SMOKE_USER", "smoke_test"))
    ap.add_argument("--password", default=os.environ.get("SMOKE_PASS", "smokepass123"))
    args = ap.parse_args()
    base = args.base.rstrip("/")

    failures = []

    def check(name, ok, detail=""):
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            failures.append(name)

    print(f"-> target: {base}  user: {args.user}")
    if not wait_ready(base):
        print("[FAIL] server never became reachable at", base)
        sys.exit(1)

    follow, noredir, jar = build_opener()

    # 1. Unauthenticated root should redirect to login.
    code, _, resp = get(noredir, base + "/")
    loc = resp.headers.get("Location", "") if hasattr(resp, "headers") else ""
    check("root redirects to /login/ when unauthenticated",
          code == 302 and "/login" in loc, f"status={code} location={loc}")

    # 2. GET login form → grab CSRF form token (cookie is captured in jar).
    code, body, _ = get(follow, base + "/login/")
    m = CSRF_INPUT.search(body)
    check("login form served with CSRF token", code == 200 and bool(m), f"status={code}")
    if not m:
        _summary(failures); sys.exit(1)
    token = m.group(1)

    # 3. POST credentials through the real login form.
    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": token,
        "username": args.user,
        "password": args.password,
    }).encode()
    req = urllib.request.Request(
        base + "/login/", data=data,
        headers={"Referer": base + "/login/",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        resp = noredir.open(req, timeout=15)
        code, loc = resp.getcode(), resp.headers.get("Location", "")
    except urllib.error.HTTPError as e:
        code, loc = e.code, e.headers.get("Location", "")
    # 302 away from /login/ == success; 200 == form re-rendered with errors.
    check("login succeeds (302 away from login)",
          code == 302 and "/login" not in loc, f"status={code} location={loc or '(none)'}")

    # 4. Authenticated dashboard renders.
    code, body, _ = get(follow, base + "/")
    check("authenticated dashboard renders",
          code == 200 and "MARBIKA" in body, f"status={code}")

    # 5. DRF attendance API returns JSON (no auth configured → open).
    code, body, _ = get(follow, base + "/attendance/api/v1/attendance/")
    is_json = False
    try:
        json.loads(body); is_json = True
    except Exception:
        pass
    check("attendance API returns JSON", code == 200 and is_json,
          f"status={code} body[:60]={body[:60]!r}")

    _summary(failures)
    sys.exit(1 if failures else 0)


def _summary(failures):
    print("-" * 40)
    if failures:
        print(f"RESULT: FAIL ({len(failures)} check(s) failed): {', '.join(failures)}")
    else:
        print("RESULT: PASS - all smoke checks green")


if __name__ == "__main__":
    main()
