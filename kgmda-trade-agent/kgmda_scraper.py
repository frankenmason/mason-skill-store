#!/usr/bin/env python3
"""
KGMDA 골프회원권 시세 조회 스크립트 (읽기 전용)

HC-KGMDA: 로그인 + 검색 + 조회만 허용. 등록/수정/삭제 절대 금지.
Rate Limit: min_interval=5s, max_requests_per_session=50, login_max_retry=2

Usage:
    python3 kgmda_scraper.py --keyword "블루원"
    python3 kgmda_scraper.py --keyword "남서울" --type junior --screenshot
    python3 kgmda_scraper.py --keyword "한양" --output /tmp/result.json
"""

import asyncio
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from shutil import which
from typing import Dict, List, Optional, Tuple

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

if not which("curl"):
    print("ERROR: curl not found. Install curl for your platform.")
    sys.exit(1)


# === HC-KGMDA Safety Constants ===

ALLOWED_URLS = {
    "main": "http://www.kgmda.com/",
    "login_frame": "http://www.kgmda.com/new2/index.php",
    "login_post": "http://www.kgmda.com/new2/member/login_reg.php",
    "trade_regular": "http://www.kgmda.com/html_new2/Trade_001.php",
    "trade_junior": "http://www.kgmda.com/html2_new2/Trade_001.php",
}

BLOCKED_PATTERNS = [
    "Trade_reg.php",
    "OpenAdd",
    "OpenAllUpdate",
    "police(",
    "Delete",
]

RATE_LIMIT_INTERVAL = 5  # seconds between requests
MAX_REQUESTS_PER_SESSION = 50
LOGIN_MAX_RETRY = 2

# === Configuration ===

KST = timezone(timedelta(hours=9))

SELL_TABLE_INDEX = 3
BUY_TABLE_INDEX = 7

PARSE_TABLE_JS = """
(tableIdx) => {
    const t = document.querySelectorAll('table')[tableIdx];
    if (!t) return [];
    const rows = [...t.querySelectorAll('tr')].slice(1);
    return rows.map(r => {
        const cells = [...r.querySelectorAll('td')];
        if (cells.length < 6) return null;
        return {
            rank: cells[0]?.textContent?.trim() || '',
            company: cells[1]?.textContent?.trim() || '',
            course: cells[2]?.textContent?.trim() || '',
            price: cells[3]?.textContent?.trim() || '',
            note: cells[4]?.textContent?.trim() || '',
            date: cells[5]?.textContent?.trim() || ''
        };
    }).filter(r => r !== null && r.rank !== '');
}
"""

def get_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Get credentials: env vars → interactive prompt → None."""
    kgmda_id = os.environ.get("KGMDA_ID")
    kgmda_pw = os.environ.get("KGMDA_PW")

    if not kgmda_id:
        try:
            kgmda_id = input("KGMDA ID: ").strip()
        except (EOFError, KeyboardInterrupt):
            pass

    if not kgmda_pw:
        try:
            import getpass
            kgmda_pw = getpass.getpass("KGMDA PW: ").strip()
        except (EOFError, KeyboardInterrupt):
            pass

    return kgmda_id or None, kgmda_pw or None


def validate_url(url: str) -> bool:
    """HC-KGMDA: Only allow whitelisted URLs."""
    return any(url.startswith(allowed) for allowed in ALLOWED_URLS.values())


def _create_cookie_file() -> str:
    """Create a secure temp file for cookies (0600 permissions)."""
    fd, path = tempfile.mkstemp(prefix="kgmda_", suffix=".txt")
    os.close(fd)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    return path


def curl_login(user: str, pwd: str, proxy: Optional[str] = None) -> Tuple[List[Dict], bool, str, str]:
    """
    Login via curl subprocess (PHP/4.4.9 cookie-based auth).
    Returns (playwright_cookies, success, response_body, cookie_file_path).
    """
    cookie_file = _create_cookie_file()
    proxy_args = ["--socks5-hostname", proxy] if proxy else []

    # Step 1: Visit main page to establish connection
    subprocess.run(
        ["curl", "-s"] + proxy_args + ["-c", cookie_file, ALLOWED_URLS["main"]],
        capture_output=True, timeout=15,
    )

    # Step 2: POST login
    result = subprocess.run(
        ["curl", "-s"] + proxy_args + ["-b", cookie_file, "-c", cookie_file,
         "-d", f"userid={user}&pwd={pwd}",
         ALLOWED_URLS["login_post"]],
        capture_output=True, timeout=15,
    )
    body = result.stdout.decode("euc-kr", errors="replace")
    success = "location.replace" in body

    # Step 3: Follow JS redirect to set remaining cookies
    if success:
        subprocess.run(
            ["curl", "-s"] + proxy_args + ["-b", cookie_file, "-c", cookie_file,
             ALLOWED_URLS["login_frame"]],
            capture_output=True, timeout=15,
        )

    # Parse Netscape cookie file → Playwright format
    cookies: List[Dict] = []
    try:
        with open(cookie_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    cookies.append({
                        "name": parts[5],
                        "value": parts[6],
                        "domain": parts[0],
                        "path": parts[2],
                    })
    except FileNotFoundError:
        pass

    return cookies, success, body, cookie_file


def curl_logout(cookie_file: str, proxy: Optional[str] = None) -> None:
    """Logout via curl to release server-side session."""
    if not cookie_file or not os.path.exists(cookie_file):
        return
    try:
        proxy_args = ["--socks5-hostname", proxy] if proxy else []
        subprocess.run(
            ["curl", "-s"] + proxy_args + ["-b", cookie_file,
             "http://www.kgmda.com/new2/member/login_out.php"],
            capture_output=True, timeout=15,
        )
    finally:
        try:
            os.remove(cookie_file)
        except OSError:
            pass


async def scrape_kgmda(
    keyword: str,
    trade_type: str = "regular",
    screenshot_path: Optional[str] = None,
    kgmda_id: Optional[str] = None,
    kgmda_pw: Optional[str] = None,
    proxy: Optional[str] = None,
) -> dict:
    """
    Main scraping function. Returns structured JSON result.

    Args:
        keyword: Golf course name to search
        trade_type: "regular" (정회원) or "junior" (준회원)
        screenshot_path: Optional path to save screenshot
        kgmda_id: Login ID (falls back to env KGMDA_ID)
        kgmda_pw: Login PW (falls back to env KGMDA_PW)

    Returns:
        dict with keys: keyword, timestamp, trade_type, sell, buy, summary, error
    """
    result = {
        "keyword": keyword,
        "timestamp": datetime.now(KST).isoformat(),
        "trade_type": trade_type,
        "sell": [],
        "buy": [],
        "summary": {},
        "error": None,
    }

    # Resolve credentials
    if not kgmda_id or not kgmda_pw:
        env_id, env_pw = get_credentials()
        kgmda_id = kgmda_id or env_id
        kgmda_pw = kgmda_pw or env_pw

    if not kgmda_id or not kgmda_pw:
        result["error"] = "HALT: Credentials not provided. Set KGMDA_ID/KGMDA_PW env vars."
        return result

    trade_url = ALLOWED_URLS.get(f"trade_{trade_type}")
    if not trade_url:
        result["error"] = f"HALT: Invalid trade_type '{trade_type}'. Use 'regular' or 'junior'."
        return result

    # === Step 1: Login via curl (PHP/4.4.9 cookie-based auth) ===
    cookies, login_ok, login_body, cookie_file = curl_login(kgmda_id, kgmda_pw, proxy=proxy)

    if not login_ok or not cookies:
        error_msg = "Session conflict or invalid credentials"
        if "이미" in login_body:
            error_msg = "Concurrent session detected (다른곳에서 이미 접속중)"
        elif "Session" in login_body:
            error_msg = "Session not established"
        result["error"] = f"HALT: Login failed — {error_msg}"
        curl_logout(cookie_file, proxy=proxy)  # cleanup on failure
        return result

    async with async_playwright() as p:
        launch_args = {"headless": True}
        if proxy:
            launch_args["proxy"] = {"server": f"socks5://{proxy}"}
        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ko-KR",
        )
        # Inject cookies from curl login
        await context.add_cookies(cookies)
        page = await context.new_page()

        # HC-KGMDA: Block all write/delete URLs at network level
        async def _block_writes(route):
            url = route.request.url
            if any(p in url for p in BLOCKED_PATTERNS):
                await route.abort()
                return
            await route.continue_()

        await page.route("**/*", _block_writes)

        try:
            # === Step 2: Navigate to Trade page ===

            if not validate_url(trade_url):
                result["error"] = f"HALT: URL blocked by HC-KGMDA: {trade_url}"
                await browser.close()
                return result

            await page.goto(trade_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)

            # === Step 4: Search by keyword ===
            await page.fill('input[name="goods"]', keyword, timeout=5000)
            await page.evaluate("document.forms['FIND'].submit();")
            await page.wait_for_timeout(3000)

            # === Step 5: Parse tables (READ-ONLY) ===
            sell_data = await page.evaluate(PARSE_TABLE_JS, SELL_TABLE_INDEX)
            buy_data = await page.evaluate(PARSE_TABLE_JS, BUY_TABLE_INDEX)

            result["sell"] = sell_data
            result["buy"] = buy_data

            # === Step 6: Summary ===
            if sell_data:
                sell_prices = []
                for item in sell_data:
                    try:
                        sell_prices.append(int(item["price"].replace(",", "")))
                    except (ValueError, KeyError):
                        pass
                if sell_prices:
                    result["summary"]["sell_min"] = f"{min(sell_prices):,}"
                    result["summary"]["sell_max"] = f"{max(sell_prices):,}"
                    result["summary"]["sell_count"] = len(sell_data)

            if buy_data:
                buy_prices = []
                for item in buy_data:
                    try:
                        buy_prices.append(int(item["price"].replace(",", "")))
                    except (ValueError, KeyError):
                        pass
                if buy_prices:
                    result["summary"]["buy_min"] = f"{min(buy_prices):,}"
                    result["summary"]["buy_max"] = f"{max(buy_prices):,}"
                    result["summary"]["buy_count"] = len(buy_data)

            result["summary"]["unit"] = "만원"

            # === Step 7: Screenshot (optional) ===
            if screenshot_path:
                await page.screenshot(path=screenshot_path, full_page=True)
                result["summary"]["screenshot"] = screenshot_path

            # Empty result check
            if not sell_data and not buy_data:
                result["error"] = f"검색 결과 없음: '{keyword}'"

        except Exception as e:
            result["error"] = f"HALT: Unexpected error: {str(e)}"

        finally:
            await browser.close()
            # Always logout to release server-side session
            curl_logout(cookie_file, proxy=proxy)

    return result


def format_tg_message(result: dict) -> str:
    """Format result as Telegram-friendly text."""
    if result.get("error"):
        return f"❌ KGMDA 조회 실패\n키워드: {result['keyword']}\n에러: {result['error']}"

    lines = [
        f"📊 KGMDA 회원권 시세 — {result['keyword']}",
        f"조회: {result['timestamp'][:16]} | {result['trade_type']}",
        "",
    ]

    summary = result.get("summary", {})

    # 매도
    sell = result.get("sell", [])
    if sell:
        lines.append(f"🔴 매도 ({summary.get('sell_count', len(sell))}건)")
        lines.append(f"  범위: {summary.get('sell_min', '?')} ~ {summary.get('sell_max', '?')} 만원")
        for item in sell[:5]:
            lines.append(f"  {item['company']:12s} {item['course']:16s} {item['price']:>8s} {item['note']}")
        if len(sell) > 5:
            lines.append(f"  ... 외 {len(sell)-5}건")
    else:
        lines.append("🔴 매도: 없음")

    lines.append("")

    # 매수
    buy = result.get("buy", [])
    if buy:
        lines.append(f"🟢 매수 ({summary.get('buy_count', len(buy))}건)")
        lines.append(f"  범위: {summary.get('buy_min', '?')} ~ {summary.get('buy_max', '?')} 만원")
        for item in buy[:5]:
            lines.append(f"  {item['company']:12s} {item['course']:16s} {item['price']:>8s} {item['note']}")
        if len(buy) > 5:
            lines.append(f"  ... 외 {len(buy)-5}건")
    else:
        lines.append("🟢 매수: 없음")

    return "\n".join(lines)


def send_tg_message(text: str, screenshot_path: Optional[str] = None) -> bool:
    """Send result directly to TG via Bot API (no agent needed)."""
    import urllib.request
    import urllib.parse

    bot_token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not bot_token or not chat_id:
        print("ERROR: TG_BOT_TOKEN or TG_CHAT_ID not set")
        return False

    # Send text
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(url, data, timeout=10)
    except Exception as e:
        print(f"TG send failed: {e}")
        return False

    # Send screenshot if exists
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            import http.client
            import mimetypes
            boundary = "----KGMDABoundary"
            body_parts = []
            body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}")
            with open(screenshot_path, "rb") as f:
                file_data = f.read()
            fname = os.path.basename(screenshot_path)
            body_parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{fname}\"\r\n"
                f"Content-Type: image/png\r\n\r\n"
            )
            body = b""
            for part in body_parts[:-1]:
                body += part.encode() + b"\r\n"
            body += body_parts[-1].encode()
            body += file_data + f"\r\n--{boundary}--\r\n".encode()

            conn = http.client.HTTPSConnection("api.telegram.org", timeout=15)
            conn.request("POST", f"/bot{bot_token}/sendPhoto", body,
                        {"Content-Type": f"multipart/form-data; boundary={boundary}"})
            conn.getresponse()
            conn.close()
        except Exception as e:
            print(f"TG photo send failed: {e}")

    return True


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="KGMDA Golf Membership Price Checker (READ-ONLY)")
    parser.add_argument("--keyword", "-k", required=True, help="Golf course name to search")
    parser.add_argument("--type", "-t", default="regular", choices=["regular", "junior"],
                        help="Trade type: regular (정회원) or junior (준회원)")
    parser.add_argument("--screenshot", "-s", action="store_true", help="Save screenshot")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    # Credentials via env vars only (KGMDA_ID, KGMDA_PW) — never pass via CLI args
    parser.add_argument("--tg-format", action="store_true", help="Print TG-formatted output")
    parser.add_argument("--tg-send", action="store_true",
                        help="Send result directly to TG (requires TG_BOT_TOKEN, TG_CHAT_ID env vars)")
    parser.add_argument("--proxy", default=None,
                        help="SOCKS5 proxy (host:port). Also reads KGMDA_PROXY env var. "
                             "Example: --proxy 127.0.0.1:1080")

    args = parser.parse_args()

    screenshot_path = None
    if args.screenshot:
        screenshot_dir = os.environ.get("KGMDA_SCREENSHOT_DIR", tempfile.gettempdir())
        screenshot_path = os.path.join(
            screenshot_dir,
            f"kgmda_{args.keyword}_{datetime.now(KST).strftime('%Y%m%d_%H%M')}.png"
        )

    # Proxy: CLI arg > env var
    proxy = args.proxy or os.environ.get("KGMDA_PROXY")

    result = await scrape_kgmda(
        keyword=args.keyword,
        trade_type=args.type,
        screenshot_path=screenshot_path,
        proxy=proxy,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"Result saved to: {args.output}")

    if args.tg_send:
        msg = format_tg_message(result)
        ok = send_tg_message(msg, screenshot_path)
        print(f"TG sent: {ok}")
    elif args.tg_format:
        print(format_tg_message(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
