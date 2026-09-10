#!/usr/bin/env python3
"""Generate the bilingual SupplyX SSC Newsbot briefing from Google News RSS."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

BEIJING = timezone(timedelta(hours=8))
OUTPUT = Path(__file__).parents[1] / "supplyx" / "daily-briefing.html"


def fetch_news(query, limit=2):
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
    try:
        with urlopen(Request(url, headers={"User-Agent": "SupplyX-Newsbot/1.0"}), timeout=20) as response:
            root = ET.fromstring(response.read())
    except Exception as error:
        print(f"Feed unavailable for {query!r}: {error}")
        return []
    items = []
    for node in root.findall("./channel/item"):
        title, link, published = (node.findtext("title") or "").strip(), (node.findtext("link") or "").strip(), (node.findtext("pubDate") or "").strip()
        source = node.find("source")
        if title and link and published:
            items.append({"title": title, "link": link, "published": published, "source": (source.text or "Google News").strip() if source is not None else "Google News"})
        if len(items) >= limit:
            break
    return items


def news_cards(items, zh_fallback, en_fallback, zh_tip, en_tip):
    if not items:
        return f'<article class="item"><h3 data-zh="{zh_fallback[0]}" data-en="{en_fallback[0]}">{zh_fallback[0]}</h3><p data-zh="{zh_fallback[1]}" data-en="{en_fallback[1]}">{zh_fallback[1]}</p><p class="tip" data-zh="{zh_tip}" data-en="{en_tip}">{zh_tip}</p></article>'
    cards = []
    for item in items:
        try:
            date = parsedate_to_datetime(item["published"]).astimezone(BEIJING).strftime("%Y-%m-%d")
        except (TypeError, ValueError, OverflowError):
            date = item["published"]
        cards.append(f'''<article class="item"><h3><a href="{escape(item['link'], quote=True)}" target="_blank" rel="noopener">{escape(item['title'])}</a></h3><p class="meta"><span data-zh="来源" data-en="Source">来源</span>: {escape(item['source'])} · <span data-zh="发布日期" data-en="Published">发布日期</span>: {escape(date)}</p><p data-zh="<b>核心事实：</b>标题、来源与链接由 Google News RSS 抓取；请进入原文核验完整细节。" data-en="<b>Key fact:</b> Title, publisher, and link were captured from Google News RSS. Verify details in the original report."><b>核心事实：</b>标题、来源与链接由 Google News RSS 抓取；请进入原文核验完整细节。</p><p class="tip" data-zh="{zh_tip}" data-en="{en_tip}">{zh_tip}</p></article>''')
    return "".join(cards)


def build_page(now, technology, industry):
    date = now.strftime("%Y-%m-%d")
    tech = news_cards(technology, ("AI 驱动的供应链例外管理", "优先梳理延误、缺料和需求异常的识别规则，并把人工审批嵌入执行链路。"), ("AI-enabled supply chain exception management", "Prioritize rules for delays, shortages, and demand anomalies, with human approval embedded in execution."), "影响/启示：评估自动化建议对计划、仓储与运输约束的影响。", "Implication: Assess how automated recommendations affect planning, warehousing, and transport constraints.")
    industry_html = news_cards(industry, ("端到端交期风险监控", "将承运人 ETA、港口拥堵、清关状态和工厂产能汇入同一例外清单。"), ("End-to-end lead-time risk monitoring", "Bring carrier ETA, port congestion, customs status, and plant capacity into a single exception list."), "影响/启示：用订单级影响而非新闻热度决定升级优先级。", "Implication: Prioritize escalation by order-level impact, not headline volume.")
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>SupplyX SSC Newsbot | {date}</title><style>
:root{{--ink:#172b3a;--muted:#5c6d75;--line:#d7e2e2;--paper:#f4f5ee;--surface:#fffefa;--green:#006b63;--rust:#bd4e2c;--yellow:#f2b544;--blue:#195c78}}*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:var(--paper);font:16px/1.75 Georgia,"Noto Serif SC","Songti SC",serif}}.masthead{{color:#fffdf7;background:#173d47;border-bottom:6px solid var(--yellow)}}.masthead-inner,main,footer{{width:min(1040px,calc(100% - 40px));margin:auto}}.masthead-inner{{position:relative;padding:42px 0 34px}}h1,h2,h3,button{{font-family:"Microsoft YaHei","Noto Sans SC",sans-serif;letter-spacing:0}}h1{{margin:0;font-size:clamp(30px,5vw,48px);line-height:1.2}}.eyebrow{{margin:0 0 10px;color:#f3c85b;font:700 12px/1.2 "Segoe UI",sans-serif;letter-spacing:.12em;text-transform:uppercase}}.subhead{{margin:13px 0 0;color:#d5e4de;font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}}.language{{position:absolute;top:18px;right:0;display:flex;border:1px solid #91aaa6;border-radius:4px;overflow:hidden}}.language button{{padding:6px 9px;color:#dbeae5;border:0;background:transparent;cursor:pointer;font-size:12px}}.language button.active{{color:#173d47;background:#f2c65c}}main{{padding:30px 0 54px}}.notice{{margin-bottom:28px;padding:14px 17px;color:#514218;background:#fff4ce;border-left:4px solid var(--yellow);font:14px/1.65 "Microsoft YaHei",sans-serif}}.layout{{display:grid;grid-template-columns:minmax(0,1fr) 275px;gap:34px}}section{{margin-bottom:35px}}h2{{display:flex;align-items:center;gap:9px;margin:0 0 13px;padding-bottom:9px;border-bottom:1px solid var(--line);font-size:21px}}h2::before{{width:10px;height:10px;background:var(--rust);content:""}}.item{{padding:17px 0 18px;border-bottom:1px solid var(--line)}}.item h3{{margin:0 0 6px;font-size:17px}}.item p{{margin:5px 0}}.meta{{color:var(--muted);font:12px/1.5 "Segoe UI","Microsoft YaHei",sans-serif}}.tip{{color:var(--green);font-size:14px}}a{{color:var(--blue);text-underline-offset:3px}}.knowledge,.action,aside{{background:var(--surface);padding:20px}}.knowledge{{border-top:3px solid var(--green)}}.action{{border-left:4px solid var(--rust)}}table{{width:100%;border-collapse:collapse;font:14px/1.55 "Segoe UI","Microsoft YaHei",sans-serif}}th,td{{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:white;background:var(--blue)}}aside{{align-self:start;border-top:4px solid var(--green);font-family:"Microsoft YaHei",sans-serif}}aside h2{{font-size:17px}}aside h2::before{{background:var(--green)}}aside ul{{margin:0;padding-left:19px}}footer{{padding:22px 0 35px;color:var(--muted);border-top:1px solid var(--line);font:12px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}}@media(max-width:760px){{.masthead-inner,main,footer{{width:min(100% - 28px,1040px)}}.masthead-inner{{padding:58px 0 27px}}.language{{top:16px}}.layout{{grid-template-columns:1fr}}aside{{margin-bottom:30px}}}}</style></head>
<body><header class="masthead"><div class="masthead-inner"><div class="language"><button id="zh" class="active" type="button">中文</button><button id="en" type="button">EN</button></div><p class="eyebrow">SupplyX / Supply Chain Intelligence</p><h1>SupplyX SSC Newsbot</h1><p class="subhead" data-zh="全球供应链每日简报｜{date}｜阅读时间：约 4 分钟" data-en="Global Supply Chain Daily Briefing | {date} | 4 min read">全球供应链每日简报｜{date}｜阅读时间：约 4 分钟</p></div></header><main><div class="layout"><article><section><h2 data-zh="技术前沿" data-en="Technology Frontiers">技术前沿</h2>{tech}</section><section><h2 data-zh="行业动态" data-en="Industry Developments">行业动态</h2>{industry_html}</section><section><h2 data-zh="知识科普：供应链控制塔" data-en="Explainer: Supply Chain Control Tower">知识科普：供应链控制塔</h2><div class="knowledge"><p data-zh="<b>一句话定义：</b>控制塔汇集跨部门、跨企业数据，用于发现例外、评估影响并协调行动。" data-en="<b>Definition:</b> A control tower unifies cross-functional and partner data to detect exceptions, assess impact, and coordinate action."><b>一句话定义：</b>控制塔汇集跨部门、跨企业数据，用于发现例外、评估影响并协调行动。</p><p data-zh="<b>常见误区：</b>先买平台再补数据治理；没有统一主数据、规则和责任人，控制塔只会放大噪声。" data-en="<b>Common misconception:</b> Buying a platform before fixing data governance. Without common master data, rules, and owners, it only amplifies noise."><b>常见误区：</b>先买平台再补数据治理；没有统一主数据、规则和责任人，控制塔只会放大噪声。</p></div></section><section><h2 data-zh="数据速览" data-en="Data Watch">数据速览</h2><table><thead><tr><th data-zh="指标" data-en="Metric">指标</th><th data-zh="数值/变化" data-en="Value / change">数值/变化</th><th data-zh="来源" data-en="Source">来源</th></tr></thead><tbody><tr><td data-zh="集装箱运价" data-en="Container freight rates">集装箱运价</td><td data-zh="请查阅最新指数" data-en="See latest index">请查阅最新指数</td><td><a href="https://www.drewry.co.uk/supply-chain-advisors/supply-chain-expertise/world-container-index" target="_blank" rel="noopener">Drewry World Container Index</a></td></tr><tr><td data-zh="全球贸易数据" data-en="Global trade data">全球贸易数据</td><td data-zh="请查阅最新统计" data-en="See latest statistics">请查阅最新统计</td><td><a href="https://www.wto.org/english/res_e/statis_e/trade_profiles_e/trade_profiles_e.htm" target="_blank" rel="noopener">WTO Statistics</a></td></tr></tbody></table></section><section><h2 data-zh="今日行动建议" data-en="Actions for Today">今日行动建议</h2><div class="action" data-zh="1. 对未来两周重点订单，建立“承诺交期 - 供应可得性 - 在途 ETA”核对表，对任一偏差指定升级负责人。<br>2. 在自动化采购或计划建议进入执行前，记录数据版本、约束条件与人工审批结论。" data-en="1. For priority orders in the next two weeks, reconcile committed date, supply availability, and in-transit ETA; assign an escalation owner to each variance.<br>2. Before automated planning or procurement recommendations are executed, record the data version, constraints, and human approval decision.">1. 对未来两周重点订单，建立“承诺交期 - 供应可得性 - 在途 ETA”核对表，对任一偏差指定升级负责人。<br>2. 在自动化采购或计划建议进入执行前，记录数据版本、约束条件与人工审批结论。</div></section></article><aside><h2 data-zh="信息来源" data-en="Sources">信息来源</h2><ul><li><a href="https://www.reuters.com/" target="_blank" rel="noopener">Reuters</a></li><li><a href="https://www.supplychaindive.com/" target="_blank" rel="noopener">Supply Chain Dive</a></li><li><a href="https://www.freightwaves.com/" target="_blank" rel="noopener">FreightWaves</a></li><li><a href="https://www.iata.org/en/publications/economics/" target="_blank" rel="noopener">IATA Economics</a></li></ul></aside></div></main><footer>SupplyX SSC Newsbot</footer><script>const setLanguage=l=>{{document.documentElement.lang=l==='en'?'en':'zh-CN';document.querySelectorAll('[data-zh]').forEach(e=>e.innerHTML=e.dataset[l]);document.querySelectorAll('.language button').forEach(b=>b.classList.toggle('active',b.id===l));localStorage.setItem('supplyx-language',l)}};document.querySelectorAll('.language button').forEach(b=>b.onclick=()=>setLanguage(b.id));setLanguage(localStorage.getItem('supplyx-language')||'zh');</script></body></html>'''


def main():
    now = datetime.now(BEIJING)
    OUTPUT.write_text(build_page(now, fetch_news('supply chain AI OR warehouse robotics OR digital twin'), fetch_news('supply chain logistics trade policy port freight')), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()