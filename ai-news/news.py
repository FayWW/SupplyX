#!/usr/bin/env python3
"""
AIHOT Daily AI News Briefing - Auto Push
Data source: aihot.virxact.com (free API, no key required)
Push: Email (126.com) + WeChat (PushPlus)
Usage: python news.py  (auto send, no confirmation needed)
"""

import subprocess, sys, os

# -- Auto install dependencies --
def ensure_deps():
    for pkg in ["requests", "schedule"]:
        try: __import__(pkg)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg])

ensure_deps()

import json, smtplib, ssl, time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import schedule as sched_lib

# ====================================================
# Config
# ====================================================

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "sender_email": "",
    "sender_password": "",
    "recipient_email": "",
    "pushplus_token": "",
    "schedule_time": "09:55",
}

SMTP_PROVIDERS = {
    "gmail.com":   {"host": "smtp.gmail.com",      "port": 587, "tls": "starttls"},
    "outlook.com": {"host": "smtp.office365.com",  "port": 587, "tls": "starttls"},
    "hotmail.com": {"host": "smtp.office365.com",  "port": 587, "tls": "starttls"},
    "qq.com":      {"host": "smtp.qq.com",         "port": 465, "tls": "ssl"},
    "foxmail.com": {"host": "smtp.qq.com",         "port": 465, "tls": "ssl"},
    "163.com":     {"host": "smtp.163.com",        "port": 465, "tls": "ssl"},
    "126.com":     {"host": "smtp.126.com",        "port": 465, "tls": "ssl"},
    "yeah.net":    {"host": "smtp.yeah.net",        "port": 465, "tls": "ssl"},
    "sina.com":    {"host": "smtp.sina.com",        "port": 465, "tls": "ssl"},
    "aliyun.com":  {"host": "smtp.aliyun.com",     "port": 465, "tls": "ssl"},
    "yahoo.com":   {"host": "smtp.mail.yahoo.com", "port": 465, "tls": "ssl"},
    "139.com":     {"host": "smtp.139.com",        "port": 465, "tls": "ssl"},
    "icloud.com":  {"host": "smtp.mail.me.com",    "port": 587, "tls": "starttls"},
}

AIHOT_API = "https://aihot.virxact.com/api/v1"
AIHOT_UA = "aihot-api/1.0 daily-briefing-bot"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def detect_smtp(email):
    domain = email.strip().lower().split("@")[-1]
    return SMTP_PROVIDERS.get(domain, {"host": f"smtp.{domain}", "port": 587, "tls": "starttls"})


# ====================================================
# AIHOT API - Fetch Data
# ====================================================

def api_get(path, params=None):
    """Call AIHOT API with retry"""
    url = f"{AIHOT_API}{path}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, headers={"User-Agent": AIHOT_UA}, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                retry = int(resp.headers.get("Retry-After", 10))
                print(f"  [!] Rate limited, waiting {retry}s...")
                time.sleep(retry)
            else:
                print(f"  [!] API {path} returned {resp.status_code}")
                return None
        except Exception as e:
            print(f"  [!] API {path} error: {e}")
            if attempt < 2:
                time.sleep(3)
    return None


def fetch_hot_topics():
    """Fetch current hot topics from AIHOT"""
    data = api_get("/hot-topics")
    if not data:
        return []
    items = []
    for it in data.get("items", [])[:10]:
        items.append({
            "rank": it.get("rank", 0),
            "title": it.get("title", ""),
            "source": it.get("source", {}).get("name", ""),
            "link": it.get("links", {}).get("aihot", ""),
            "original": it.get("links", {}).get("original", ""),
            "source_count": it.get("sourceCount", 1),
        })
    print(f"  Hot Topics: {len(items)} items")
    return items


def fetch_daily_report():
    """Fetch latest daily report from AIHOT"""
    data = api_get("/dailies/latest")
    if not data or not data.get("report"):
        return None
    report = data["report"]
    sections = []
    for sec in report.get("sections", []):
        section = {"label": sec.get("label", ""), "items": []}
        for it in sec.get("items", []):
            section["items"].append({
                "title": it.get("title", ""),
                "summary": it.get("summary", ""),
                "source": it.get("source", {}).get("name", ""),
                "link": it.get("links", {}).get("aihot", ""),
                "original": it.get("links", {}).get("original", ""),
            })
        sections.append(section)
    print(f"  Daily Report: {len(sections)} sections")
    return {"date": report.get("date", ""), "sections": sections}


def fetch_latest_items():
    """Fetch latest 24h selected items from AIHOT"""
    data = api_get("/items", params={"mode": "selected", "window": "24h", "limit": 15})
    if not data:
        return []
    items = []
    for it in data.get("items", []):
        cat = it.get("category", "")
        cat_map = {
            "ai-models": "AI模型", "ai-products": "AI产品",
            "industry": "行业动态", "paper": "论文研究",
            "tip": "教程技巧", "opinion": "观点",
        }
        items.append({
            "title": it.get("title", ""),
            "summary": it.get("summary", "") or it.get("reason", "") or "",
            "source": it.get("source", {}).get("name", ""),
            "link": it.get("links", {}).get("aihot", ""),
            "original": it.get("links", {}).get("original", ""),
            "category": cat_map.get(cat, cat),
            "score": it.get("score", 0),
        })
    print(f"  Latest Items: {len(items)} items")
    return items


# ====================================================
# Email HTML Template
# ====================================================

CATEGORY_COLORS = {
    "AI模型": "#7c3aed", "AI产品": "#2563eb", "行业动态": "#059669",
    "论文研究": "#d97706", "教程技巧": "#0891b2", "观点": "#dc2626",
    "模型发布/更新": "#7c3aed", "产品发布/更新": "#2563eb",
    "技巧与观点": "#0891b2",
}
CATEGORY_ICONS = {
    "模型发布/更新": "&#129504;", "产品发布/更新": "&#128640;",
    "行业动态": "&#127758;", "论文研究": "&#128218;",
    "技巧与观点": "&#128161;", "观点": "&#128172;",
}

def build_html(hot_topics, daily, latest_items):
    bj = timezone(timedelta(hours=8))
    now = datetime.now(bj)
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M")
    wd_map = {0:"一",1:"二",2:"三",3:"四",4:"五",5:"六",6:"日"}
    weekday = f"星期{wd_map[now.weekday()]}"

    # --- Hot Topics ---
    hot_rows = ""
    if hot_topics:
        for it in hot_topics:
            r = it["rank"]
            if r == 1:
                bg = "linear-gradient(135deg,#ef4444,#f97316)"; sz = "26"; fsz = "13"
            elif r <= 3:
                bg = "linear-gradient(135deg,#f97316,#eab308)"; sz = "24"; fsz = "12"
            else:
                bg = "#cbd5e1"; sz = "22"; fsz = "11"
            link = it.get("original") or it.get("link", "#")
            sc = it["source_count"]
            heat = f'<span style="display:inline-block;background:#fef2f2;color:#dc2626;font-size:10px;padding:2px 8px;border-radius:10px;margin-left:6px;font-weight:600;letter-spacing:0.3px;">{sc} 源</span>' if sc > 1 else ""
            hot_rows += (
                f'<tr><td style="padding:10px 0;border-bottom:1px solid #f1f5f9;vertical-align:top;width:40px;">'
                f'<div style="width:{sz}px;height:{sz}px;background:{bg};color:#fff;font-size:{fsz}px;'
                f'font-weight:800;border-radius:50%;text-align:center;line-height:{sz}px;">{r}</div></td>'
                f'<td style="padding:10px 0 10px 12px;border-bottom:1px solid #f1f5f9;vertical-align:top;">'
                f'<a href="{link}" style="color:#0f172a;text-decoration:none;font-size:14px;font-weight:600;line-height:1.5;">{it["title"]}</a>{heat}'
                f'<br/><span style="font-size:11px;color:#94a3b8;">{it["source"]}</span></td></tr>'
            )

    # --- Daily Report ---
    daily_blocks = ""
    if daily and daily.get("sections"):
        for sec in daily["sections"]:
            label = sec["label"]
            color = CATEGORY_COLORS.get(label, "#475569")
            icon = CATEGORY_ICONS.get(label, "&#9679;")
            items_rows = ""
            for it in sec["items"]:
                summary = it.get("summary", "")
                if len(summary) > 130:
                    summary = summary[:127] + "..."
                link = it.get("original") or it.get("link", "#")
                items_rows += (
                    f'<tr><td style="padding:10px 0 10px 16px;border-bottom:1px solid #f8fafc;vertical-align:top;">'
                    f'<a href="{link}" style="color:#1e293b;text-decoration:none;font-size:13px;font-weight:600;line-height:1.5;">{it["title"]}</a>'
                    f'<p style="margin:4px 0 0 0;font-size:12px;color:#64748b;line-height:1.6;">{summary}</p>'
                    f'<p style="margin:4px 0 0 0;font-size:11px;color:#94a3b8;">{it["source"]}</p>'
                    f'</td></tr>'
                )
            daily_blocks += (
                f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:20px;">'
                f'<tr><td style="padding:10px 14px;background:{color}0d;border-left:3px solid {color};border-radius:0 6px 6px 0;">'
                f'<span style="font-size:15px;font-weight:700;color:{color};">{icon} {label}</span>'
                f'<span style="float:right;font-size:11px;color:#94a3b8;line-height:24px;">{len(sec["items"])} 条</span>'
                f'</td></tr>{items_rows}</table>'
            )

    # --- Latest Items (fallback) ---
    items_rows = ""
    if latest_items and not daily:
        for i, it in enumerate(latest_items[:10], 1):
            cat = it.get("category", "")
            color = CATEGORY_COLORS.get(cat, "#475569")
            summary = it.get("summary", "")
            if len(summary) > 130:
                summary = summary[:127] + "..."
            link = it.get("original") or it.get("link", "#")
            score = it.get("score", 0)
            sc_bg = "#fef2f2" if score >= 80 else "#fffbeb" if score >= 60 else "#f1f5f9"
            sc_cl = "#dc2626" if score >= 80 else "#d97706" if score >= 60 else "#64748b"
            cat_html = f'<span style="display:inline-block;background:{color}12;color:{color};font-size:10px;padding:2px 8px;border-radius:10px;margin-right:6px;font-weight:600;">{cat}</span>' if cat else ""
            score_html = f'<span style="display:inline-block;background:{sc_bg};color:{sc_cl};font-size:10px;padding:2px 8px;border-radius:10px;font-weight:700;">AI {score}</span>'
            items_rows += (
                f'<tr><td style="padding:12px 0;border-bottom:1px solid #f1f5f9;vertical-align:top;width:36px;">'
                f'<div style="width:28px;height:28px;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;font-size:12px;font-weight:800;border-radius:8px;text-align:center;line-height:28px;">{i}</div></td>'
                f'<td style="padding:12px 0 12px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top;">'
                f'{cat_html}{score_html}'
                f'<br/><a href="{link}" style="color:#0f172a;text-decoration:none;font-size:13px;font-weight:600;line-height:1.6;margin-top:4px;display:inline-block;">{it["title"]}</a>'
                f'<p style="margin:4px 0 0 0;font-size:12px;color:#64748b;line-height:1.6;">{summary}</p>'
                f'<p style="margin:4px 0 0 0;font-size:11px;color:#94a3b8;">{it["source"]}</p>'
                f'</td></tr>'
            )

    # --- Assemble ---
    body_sections = ""

    # Header
    body_sections += (
        f'<tr><td style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 60%,#334155 100%);padding:32px 32px 28px 32px;">'
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td><h1 style="margin:0;font-size:24px;color:#fff;font-weight:800;letter-spacing:-0.3px;">AIHOT Daily</h1>'
        f'<p style="margin:8px 0 0 0;font-size:13px;color:#94a3b8;line-height:1.5;">{date_str} {weekday}</p></td>'
        f'<td style="text-align:right;vertical-align:bottom;"><span style="font-size:11px;color:#64748b;">&#128338; {time_str} BJT</span></td>'
        f'</tr></table></td></tr>'
    )

    # Hot Topics
    if hot_rows:
        body_sections += (
            f'<tr><td style="padding:28px 32px 20px 32px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px;"><tr>'
            f'<td><h2 style="margin:0;font-size:18px;color:#0f172a;font-weight:800;">&#128293; AI 热点榜</h2></td>'
            f'<td style="text-align:right;"><span style="font-size:11px;color:#94a3b8;background:#f8fafc;padding:4px 10px;border-radius:12px;">48h Top 10</span></td>'
            f'</tr></table>'
            f'<table width="100%" cellpadding="0" cellspacing="0">{hot_rows}</table>'
            f'</td></tr>'
        )

    # Divider
    body_sections += '<tr><td style="padding:0 32px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="border-bottom:2px solid #e2e8f0;height:1px;font-size:0;">&nbsp;</td></tr></table></td></tr>'

    # Daily or Items
    if daily_blocks:
        body_sections += (
            f'<tr><td style="padding:24px 32px 20px 32px;">'
            f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:8px;"><tr>'
            f'<td><h2 style="margin:0;font-size:18px;color:#0f172a;font-weight:800;">&#128240; AI 日报</h2></td>'
            f'<td style="text-align:right;"><span style="font-size:11px;color:#94a3b8;background:#f8fafc;padding:4px 10px;border-radius:12px;">AIHOT Daily</span></td>'
            f'</tr></table>'
            f'{daily_blocks}'
            f'</td></tr>'
        )
    elif items_rows:
        body_sections += (
            f'<tr><td style="padding:24px 32px 20px 32px;">'
            f'<h2 style="margin:0 0 16px 0;font-size:18px;color:#0f172a;font-weight:800;">&#129302; AI 精选</h2>'
            f'<table width="100%" cellpadding="0" cellspacing="0">{items_rows}</table>'
            f'</td></tr>'
        )

    # Footer
    body_sections += (
        f'<tr><td style="background:#f8fafc;padding:24px 32px;border-top:2px solid #e2e8f0;">'
        f'<table width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td style="text-align:right;font-size:11px;color:#cbd5e1;">Auto-generated</td>'
        f'</tr></table></td></tr>'
    )

    return (
        f'<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"/>'
        f'<meta name="viewport" content="width=device-width,initial-scale=1.0"/>'
        f'<title>AIHOT Daily {date_str}</title></head>'
        f'<body style="margin:0;padding:0;background:#e2e8f0;'
        f'font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;">'
        f'<table width="100%" cellpadding="0" cellspacing="0" style="background:#e2e8f0;padding:24px 0;">'
        f'<tr><td align="center">'
        f'<table width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;background:#ffffff;'
        f'border-radius:16px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,0.08);">'
        f'{body_sections}'
        f'</table></td></tr></table></body></html>'
    )


# ====================================================
# WeChat Content (simplified for PushPlus)
# ====================================================

def build_wechat_content(hot_topics, daily, latest_items):
    bj = timezone(timedelta(hours=8))
    now = datetime.now(bj)
    date_str = now.strftime("%Y年%m月%d日")

    lines = [f"<h2>AIHOT Daily</h2><p>{date_str}</p><hr/>"]

    # Hot Topics
    if hot_topics:
        lines.append("<h3>AI 热点榜</h3>")
        for it in hot_topics:
            src_note = f" ({it['source_count']}源)" if it["source_count"] > 1 else ""
            lines.append(f"<p><b>{it['rank']}. {it['title']}</b>{src_note}<br/><small>{it['source']}</small></p>")

    # Daily Report
    if daily and daily.get("sections"):
        lines.append("<hr/><h3>AI 日报</h3>")
        for sec in daily["sections"]:
            lines.append(f"<p><b>{sec['label']}</b></p>")
            for it in sec["items"]:
                summary = it.get("summary", "")
                if len(summary) > 80:
                    summary = summary[:77] + "..."
                lines.append(f"<p>- {it['title']}<br/><small>{summary}</small></p>")
    elif latest_items:
        lines.append("<hr/><h3>AI 精选</h3>")
        for i, it in enumerate(latest_items[:10], 1):
            cat = it.get("category", "")
            summary = it.get("summary", "")
            if len(summary) > 80:
                summary = summary[:77] + "..."
            lines.append(f"<p><b>{i}. {it['title']}</b> [{cat}]<br/><small>{summary}</small></p>")

    lines.append("<hr/><p><small>Data: aihot.virxact.com</small></p>")
    return "\n".join(lines)


# ====================================================
# Email Send
# ====================================================

def send_email(cfg, html):
    sender = cfg["sender_email"]
    password = cfg["sender_password"]
    recipient = cfg["recipient_email"]
    smtp = detect_smtp(sender)

    bj = timezone(timedelta(hours=8))
    today = datetime.now(bj).strftime("%m/%d")
    subject = f"AIHOT Daily [{today}] AI 热点 + 日报"

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AIHOT Daily <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText("Please use an HTML email client.", "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if smtp["tls"] == "ssl":
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp["host"], smtp["port"], context=ctx, timeout=30) as s:
                s.login(sender, password)
                s.send_message(msg)
        else:
            with smtplib.SMTP(smtp["host"], smtp["port"], timeout=30) as s:
                s.ehlo(); s.starttls(context=ssl.create_default_context()); s.ehlo()
                s.login(sender, password)
                s.send_message(msg)
        print(f"  Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"  Email failed: {e}")
        return False


# ====================================================
# WeChat Push (PushPlus)
# ====================================================

def send_wechat(cfg, content):
    token = cfg.get("pushplus_token", "")
    if not token:
        return False

    bj = timezone(timedelta(hours=8))
    today = datetime.now(bj).strftime("%m/%d")

    try:
        resp = requests.post(
            "http://www.pushplus.plus/send",
            json={"token": token, "title": f"AIHOT Daily [{today}]", "content": content, "template": "html"},
            timeout=30,
        )
        data = resp.json()
        if data.get("code") == 200:
            print(f"  WeChat push OK")
            return True
        else:
            print(f"  WeChat push failed: {data.get('msg', 'unknown')}")
            return False
    except Exception as e:
        print(f"  WeChat push failed: {e}")
        return False


# ====================================================
# Main Pipeline
# ====================================================

def run_once():
    cfg = load_config()
    print("\n" + "=" * 50)
    print("  AIHOT Daily Briefing - Generating...")
    print("=" * 50)

    print("\n[1/3] Fetching AIHOT data...")
    hot_topics = fetch_hot_topics()
    daily = fetch_daily_report()
    latest_items = fetch_latest_items()

    if not hot_topics and not daily and not latest_items:
        print("  [!] All API calls failed. Check network.")
        return

    print("[2/3] Building content...")
    html = build_html(hot_topics, daily, latest_items)
    wechat = build_wechat_content(hot_topics, daily, latest_items)

    # Save local copy
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "latest_briefing.html")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("[3/3] Sending...")
    if cfg.get("sender_email") and cfg.get("sender_password") and cfg.get("recipient_email"):
        send_email(cfg, html)
    send_wechat(cfg, wechat)

    print("\n  Done!\n")


def run_schedule():
    cfg = load_config()
    t = cfg.get("schedule_time", "09:55")
    print(f"\n  Scheduler started: daily at {t}")
    print("  Keep this window open. Ctrl+C to stop.\n")
    sched_lib.every().day.at(t).do(run_once)
    while True:
        sched_lib.run_pending()
        time.sleep(30)


# ====================================================
# Entry - Auto run, no confirmation
# ====================================================

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--schedule" in args:
        run_schedule()
    else:
        # Default: run once immediately (no menu, no confirmation)
        run_once()
