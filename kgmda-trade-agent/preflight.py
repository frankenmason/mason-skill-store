#!/usr/bin/env python3
"""
kgmda-trade-agent 사전 점검 스크립트

스킬 사용 전 환경 요건을 자동 검증합니다.
모든 항목 PASS 후 kgmda_scraper.py 실행 가능.
"""

import os
import sys
import subprocess
from shutil import which


def check(name, ok, msg_pass="", msg_fail=""):
    status = "PASS" if ok else "FAIL"
    symbol = "[v]" if ok else "[X]"
    detail = msg_pass if ok else msg_fail
    print(f"  {symbol} {name}: {status} {detail}")
    return ok


def main():
    print("=" * 50)
    print("kgmda-trade-agent Preflight Check")
    print("=" * 50)
    results = []

    # 1. System
    print("\n[1] System")

    # Python version
    v = sys.version_info
    results.append(check(
        "Python 3.9+",
        v.major == 3 and v.minor >= 9,
        f"({v.major}.{v.minor}.{v.micro})",
        f"({v.major}.{v.minor} — 3.9+ required)"
    ))

    # curl
    results.append(check(
        "curl",
        which("curl") is not None,
        f"({which('curl')})",
        "(not found — install curl)"
    ))

    # Internet
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "5", "http://www.kgmda.com/"],
            capture_output=True, text=True, timeout=10
        )
        internet_ok = r.stdout.strip() == "200"
    except Exception:
        internet_ok = False
    results.append(check(
        "kgmda.com accessible",
        internet_ok,
        "",
        "(cannot reach kgmda.com — check network/firewall)"
    ))

    # IP location (warn only)
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "3", "https://ipinfo.io/country"],
            capture_output=True, text=True, timeout=5
        )
        country = r.stdout.strip()
        is_kr = country == "KR"
    except Exception:
        country = "?"
        is_kr = False
    warn_symbol = "[v]" if is_kr else "[!]"
    print(f"  {warn_symbol} Korean IP: {'YES' if is_kr else 'WARN'} (country={country}) {'— non-KR IP may be blocked' if not is_kr else ''}")

    # Proxy check (relevant if non-KR IP)
    proxy = os.environ.get("KGMDA_PROXY")
    if proxy:
        print(f"  [v] KGMDA_PROXY: SET ({proxy})")
        # Test proxy connectivity
        try:
            r = subprocess.run(
                ["curl", "-s", "--socks5-hostname", proxy,
                 "-o", "/dev/null", "-w", "%{http_code}",
                 "--max-time", "10", "http://www.kgmda.com/"],
                capture_output=True, text=True, timeout=15
            )
            proxy_ok = r.stdout.strip() == "200"
        except Exception:
            proxy_ok = False
        results.append(check(
            "Proxy → kgmda.com",
            proxy_ok,
            "",
            "(proxy cannot reach kgmda.com — check tunnel)"
        ))
    elif not is_kr:
        print(f"  [!] KGMDA_PROXY: NOT SET — required for non-KR IP (set KGMDA_PROXY=host:port)")

    # 2. Python packages
    print("\n[2] Python Packages")

    try:
        from playwright.async_api import async_playwright
        pw_ok = True
    except ImportError:
        pw_ok = False
    results.append(check(
        "playwright",
        pw_ok,
        "",
        "(run: pip install playwright)"
    ))

    # Chromium
    try:
        r = subprocess.run(
            ["python3", "-c",
             "from playwright.sync_api import sync_playwright; "
             "p=sync_playwright().start(); b=p.chromium.launch(headless=True); "
             "b.close(); p.stop(); print('OK')"],
            capture_output=True, text=True, timeout=30
        )
        chromium_ok = "OK" in r.stdout
    except Exception:
        chromium_ok = False
    results.append(check(
        "chromium browser",
        chromium_ok,
        "",
        "(run: playwright install chromium)"
    ))

    # 3. Credentials
    print("\n[3] Credentials")

    kgmda_id = os.environ.get("KGMDA_ID")
    kgmda_pw = os.environ.get("KGMDA_PW")
    has_env = bool(kgmda_id and kgmda_pw)
    env_symbol = "[v]" if has_env else "[!]"
    print(f"  {env_symbol} KGMDA_ID/PW env: {'SET' if has_env else 'NOT SET (will prompt at runtime)'}")

    # 4. TG (optional)
    print("\n[4] Telegram (optional)")

    tg_token = os.environ.get("TG_BOT_TOKEN")
    tg_chat = os.environ.get("TG_CHAT_ID")
    has_tg = bool(tg_token and tg_chat)
    tg_symbol = "[v]" if has_tg else "[-]"
    print(f"  {tg_symbol} TG_BOT_TOKEN/TG_CHAT_ID: {'SET' if has_tg else 'NOT SET (--tg-send disabled)'}")

    if has_tg:
        try:
            import urllib.request
            import urllib.parse
            url = f"https://api.telegram.org/bot{tg_token}/getMe"
            r = urllib.request.urlopen(url, timeout=5)
            tg_ok = r.status == 200
        except Exception:
            tg_ok = False
        results.append(check(
            "TG Bot reachable",
            tg_ok,
            "",
            "(bot token invalid or network error)"
        ))

    # Summary
    print("\n" + "=" * 50)
    fail_count = sum(1 for r in results if not r)
    if fail_count == 0:
        print("ALL CHECKS PASSED — ready to use kgmda_scraper.py")
    else:
        print(f"{fail_count} CHECK(S) FAILED — fix above issues before using")
    print("=" * 50)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
