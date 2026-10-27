#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon Listing 硬指标校验器（零依赖，纯标准库）

用法:
    python3 check_listing.py listing.json
    python3 check_listing.py listing.json --json-report report.json

输入 JSON 结构（只填已有的，缺的跳过）:

{
  "site": "UK",
  "brand_forbidden": ["MyBrand", "OtherBrand"],
  "listing": {
    "title": "...",
    "item_highlights": "...",
    "bullets": ["...", "...", "...", "...", "..."],
    "description_html": "<p>...</p>",
    "description_plain": "...",
    "search_terms": "..."
  },
  "keywords": {
    "core": ["measuring cups"],
    "long_tail": ["stainless steel measuring cups"],
    "attribute": ["4 piece"],
    "scenario": ["baking"],
    "audience": ["home bakers"],
    "synonym": ["measuring jugs"],
    "alternative": ["baking accessories"]
  },
  "allocation": {
    "Title": ["measuring cups", "4 piece"],
    "Item Highlights": ["stackable", "metric markings"],
    "五点": ["stainless steel", "kitchen drawer"],
    "描述": ["home bakers"],
    "Search Terms": ["measuring jugs"]
  }
}

退出码: 0 = 无 ERROR（可能有 WARN）; 1 = 存在 ERROR; 2 = 输入错误
"""

import argparse
import json
import re
import sys

# ---------------------------------------------------------------- 常量

# Title Case 中通常小写的介词 / 冠词 / 连词
LOWER_WORDS = {
    "a", "an", "the", "and", "or", "but", "for", "of", "in", "on", "at",
    "to", "with", "from", "by",
}

# 绝对化 / 无法证明的表达（规范原文清单，判 ERROR）
ABSOLUTE_BANNED = [
    "best", "no.1", "no 1", "number one", "#1", "perfect", "guaranteed",
    "100% safe", "never", "most advanced",
]

# 疑似促销/夸大用词（语境可能合法，判 WARN，人工判断）
SUSPECT_PROMO = [
    "top rated", "bestseller", "best seller", "best-selling", "ultimate",
    "unbeatable", "cheapest", "free", "discount", "deal", "sale", "hot",
]

# 需要证据支撑的词（只提示，不判错）
EVIDENCE_REQUIRED = [
    "waterproof", "water resistant", "water-resistant", "heavy duty",
    "medical grade", "non-toxic", "nontoxic", "bpa free", "food safe",
    "food grade", "eco-friendly", "eco friendly", "biodegradable",
    "antibacterial", "hypoallergenic", "fireproof", "flame retardant",
]

ALLOWED_TAGS = {"p", "br", "b", "ul", "li"}

CATEGORY_LABEL = {
    "core": "核心词",
    "long_tail": "长尾词",
    "attribute": "属性词",
    "scenario": "场景词",
    "audience": "人群词",
    "synonym": "同义词",
    "alternative": "替代方案词",
}

MODULE_ALIAS = {
    "title": "Title",
    "item highlights": "Item Highlights",
    "highlights": "Item Highlights",
    "五点": "五点",
    "bullets": "五点",
    "描述": "描述",
    "description": "描述",
    "search terms": "Search Terms",
    "st": "Search Terms",
}

ASIN_RE = re.compile(r"\bB0[A-Z0-9]{8}\b")
TAG_RE = re.compile(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)")

# ---------------------------------------------------------------- 工具


def norm(text):
    """归一化：小写、非字母数字转空格、压缩空白。中文字符保留。"""
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _singular(tok):
    """粗糙单复数归一：仅去掉长度 >3 的词尾 s，避免误伤 bus/status 类词。"""
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def has_phrase(haystack_norm, phrase_norm):
    """短语匹配：精确子串优先；否则允许单复数差异的连续滑窗匹配。
    不放过任何"中间夹词"，避免把 different phrase 误判成已覆盖。
    """
    if not phrase_norm:
        return False
    padded = " " + haystack_norm + " "
    if (" " + phrase_norm + " ") in padded:
        return True
    kw_toks = phrase_norm.split()
    text_toks = haystack_norm.split()
    width = len(kw_toks)
    if not kw_toks or width > len(text_toks):
        return False
    kw_sing = [_singular(t) for t in kw_toks]
    for start in range(0, len(text_toks) - width + 1):
        window = [_singular(t) for t in text_toks[start:start + width]]
        if window == kw_sing:
            return True
    return False


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html or "")


class Report:
    def __init__(self):
        self.issues = []  # (level, code, module, message)
        self.metrics = []
        self.coverage = []  # (category, keyword, [modules])

    def err(self, code, module, msg):
        self.issues.append(("ERROR", code, module, msg))

    def warn(self, code, module, msg):
        self.issues.append(("WARN", code, module, msg))

    def info(self, code, module, msg):
        self.issues.append(("INFO", code, module, msg))

    def metric(self, name, value, limit=None, ok=None):
        self.metrics.append((name, value, limit, ok))

    def counts(self):
        e = sum(1 for i in self.issues if i[0] == "ERROR")
        w = sum(1 for i in self.issues if i[0] == "WARN")
        return e, w


# ---------------------------------------------------------------- 各项检查


def check_hard_metrics(data, rep):
    listing = data.get("listing", {})

    title = listing.get("title", "") or ""
    if title:
        n = len(title)
        rep.metric("Title 字符数", n, 75, n <= 75)
        if n > 75:
            rep.err("TITLE_LEN", "Title", "超过 75 字符（实际 %d），必须删到 75 以内" % n)
        elif n < 40:
            rep.warn("TITLE_SHORT", "Title", "仅 %d 字符，可能浪费了关键词位" % n)

    ih = listing.get("item_highlights", "") or ""
    if ih:
        n = len(ih)
        rep.metric("Item Highlights 字符数", n, 125, n <= 125)
        if n > 125:
            rep.err("IH_LEN", "Item Highlights", "超过 125 字符（实际 %d）" % n)
        groups = [g for g in re.split(r"[,，]", ih) if g.strip()]
        rep.metric("Item Highlights 词组数", len(groups), "4-6", 4 <= len(groups) <= 6)
        if not (4 <= len(groups) <= 6):
            rep.warn("IH_GROUPS", "Item Highlights", "词组数 %d 个，建议 4-6 个" % len(groups))

    st = listing.get("search_terms", "") or ""
    if st:
        nb = len(st.encode("utf-8"))
        rep.metric("Search Terms 字节数", nb, 250, nb <= 250)
        if nb > 250:
            rep.err("ST_BYTES", "Search Terms", "超过 250 字节（实际 %d）" % nb)
        if "," in st or "，" in st:
            rep.err("ST_COMMA", "Search Terms", "含逗号，平台会截断，去掉所有标点")
        if re.search(r"[.;:!?\"'()\[\]]", st):
            rep.warn("ST_PUNCT", "Search Terms", "含标点符号，建议全部去掉")
        words = norm(st).split()
        dup = sorted({w for w in words if words.count(w) > 1})
        if dup:
            rep.warn("ST_DUP", "Search Terms", "单词重复出现：%s" % ", ".join(dup))

    bullets = listing.get("bullets") or []
    if bullets:
        rep.metric("五点条数", len(bullets), 5, len(bullets) == 5)
        if len(bullets) != 5:
            rep.err("BULLET_COUNT", "五点", "必须 5 条，当前 %d 条" % len(bullets))
        for i, b in enumerate(bullets, 1):
            if not re.match(r"^\s*【[^】]+】", b or ""):
                rep.warn("BULLET_FMT", "五点#%d" % i,
                         "未以【卖点标题】开头，格式不符合规范输出模板")
            if len(b or "") < 40:
                rep.warn("BULLET_SHORT", "五点#%d" % i, "过短（%d 字符），可能没讲清好处" % len(b or ""))


def check_html(listing, rep):
    html = listing.get("description_html", "") or ""
    if not html:
        return
    tags = [t.lower() for t in TAG_RE.findall(html)]
    bad = sorted({t for t in tags if t not in ALLOWED_TAGS})
    if bad:
        rep.err("HTML_TAG", "HTML 描述",
                "使用了不允许的标签 <%s>，仅可用 p / br / b / ul / li" % ">, <".join(bad))
    for pat, name in [(r"style\s*=", "内联样式"), (r"<script", "脚本"),
                      (r"<img", "图片"), (r"href\s*=", "链接"), (r"class\s*=", "class 属性")]:
        if re.search(pat, html, re.I):
            rep.err("HTML_FORBIDDEN", "HTML 描述", "含%s，亚马逊后台不支持" % name)
    plain_len = len(strip_tags(html).strip())
    rep.metric("HTML 描述正文字符数", plain_len, "600-800", 600 <= plain_len <= 800)
    if not (600 <= plain_len <= 800):
        rep.warn("DESC_LEN_HTML", "HTML 描述",
                 "正文 %d 字符，建议 600-800（按类目后台限制调整）" % plain_len)

    plain = listing.get("description_plain", "") or ""
    if plain:
        if "<" in plain and ">" in plain:
            rep.err("PLAIN_TAG", "纯文本描述", "含 HTML 标签，纯文本版不应有标签")
        pl = len(plain.strip())
        rep.metric("纯文本描述字符数", pl, "600-800", 600 <= pl <= 800)
        if not (600 <= pl <= 800):
            rep.warn("DESC_LEN_PLAIN", "纯文本描述",
                     "正文 %d 字符，建议 600-800" % pl)
        # 两版一致性（粗校验：段落数与首段开头）
        segs_h = [s for s in re.split(r"</p>", html) if strip_tags(s).strip()]
        segs_p = [s for s in re.split(r"\n\s*\n", plain) if s.strip()]
        if segs_h and segs_p and abs(len(segs_h) - len(segs_p)) > 1:
            rep.warn("DESC_PARITY", "产品描述",
                     "HTML 版 %d 段 vs 纯文本版 %d 段，差异过大，需人工核对内容是否一致"
                     % (len(segs_h), len(segs_p)))


def check_titlecase(text, module, rep):
    if not text:
        return
    tokens = re.split(r"(\s+)", text)
    first_word_seen = False
    for tok in tokens:
        if not tok.strip():
            first_word_seen = True  # 冒号/破折号后视为新起点
            continue
        core = tok.strip(" ,;:!?()[]\"'")
        if not core:
            continue
        m = re.match(r"^([A-Za-z][A-Za-z'\-]*)$", core)
        if not m:
            first_word_seen = True
            continue
        w = m.group(1)
        low = w.lower()
        if first_word_seen and low in LOWER_WORDS and w[0].isupper():
            rep.err("CASE_LOWER_WORD", module,
                    "「%s」是介词/冠词/连词，句中应小写为「%s」" % (w, low))
        if first_word_seen and low not in LOWER_WORDS and w.islower() and len(w) > 2:
            rep.warn("CASE_TITLE", module, "「%s」未首字母大写（Title Case 要求）" % w)
        first_word_seen = True


def collect_text(listing):
    parts = {
        "Title": listing.get("title", "") or "",
        "Item Highlights": listing.get("item_highlights", "") or "",
        "描述": (listing.get("description_plain", "") or "")
                + " " + strip_tags(listing.get("description_html", "") or ""),
        "Search Terms": listing.get("search_terms", "") or "",
    }
    for i, b in enumerate(listing.get("bullets") or [], 1):
        parts["五点#%d" % i] = b or ""
    return parts


def check_forbidden(data, listing, rep):
    parts = collect_text(listing)
    whole = " ".join(parts.values())

    for w in ABSOLUTE_BANNED:
        pat = r"(?<![a-z])" + re.escape(w) + r"(?![a-z])"
        if re.search(pat, whole, re.I):
            where = [m for m, t in parts.items() if re.search(pat, t, re.I)]
            rep.err("BANNED_WORD", "/".join(where), "出现禁用表达「%s」" % w)

    for w in SUSPECT_PROMO:
        pat = r"(?<![a-z])" + re.escape(w) + r"(?![a-z])"
        if re.search(pat, whole, re.I):
            where = [m for m, t in parts.items() if re.search(pat, t, re.I)]
            rep.warn("PROMO_WORD", "/".join(where),
                     "「%s」疑似促销/夸大用词，确认语境合法" % w)

    for w in EVIDENCE_REQUIRED:
        pat = r"(?<![a-z])" + re.escape(w) + r"(?![a-z])"
        if re.search(pat, whole, re.I):
            where = [m for m, t in parts.items() if re.search(pat, t, re.I)]
            rep.warn("EVIDENCE_WORD", "/".join(where),
                     "「%s」需产品资料/检测报告支撑，确认有证据再用" % w)

    for b in data.get("brand_forbidden") or []:
        if b and re.search(r"(?<![a-z])" + re.escape(b.lower()) + r"(?![a-z])", whole.lower()):
            where = [m for m, t in parts.items()
                     if b.lower() in t.lower()]
            rep.err("BRAND", "/".join(where), "出现品牌名「%s」，Listing 文案不得含品牌名" % b)

    found = ASIN_RE.findall(whole)
    if found:
        rep.err("ASIN", "全模块", "文案中出现 ASIN：%s" % ", ".join(sorted(set(found))))


def check_keywords(data, listing, rep):
    kws = data.get("keywords") or {}
    if not kws:
        return
    parts = collect_text(listing)
    title_n = norm(parts.get("Title", ""))
    ih_n = norm(parts.get("Item Highlights", ""))
    st_n = norm(parts.get("Search Terms", ""))
    desc_n = norm(parts.get("描述", ""))
    bullets_n = [norm(b or "") for b in (listing.get("bullets") or [])]

    coverage_map = {}
    for cat, words in kws.items():
        for kw in words or []:
            k = norm(kw)
            if not k:
                continue
            hits = []
            if has_phrase(title_n, k):
                hits.append("Title")
            if has_phrase(ih_n, k):
                hits.append("Item Highlights")
            for i, bn in enumerate(bullets_n, 1):
                if has_phrase(bn, k):
                    hits.append("五点#%d" % i)
            if has_phrase(desc_n, k):
                hits.append("描述")
            if has_phrase(st_n, k):
                hits.append("Search Terms")
            coverage_map[(cat, kw)] = hits
            rep.coverage.append((CATEGORY_LABEL.get(cat, cat), kw, hits))

    def rate(cat):
        words = [w for w in (kws.get(cat) or []) if norm(w)]
        if not words:
            return None
        hit = sum(1 for w in words if coverage_map.get((cat, w)))
        return hit, len(words)

    core = rate("core")
    if core:
        rep.metric("核心词覆盖率", "%d/%d" % core, "100%", core[0] == core[1])
        if core[0] < core[1]:
            miss = [w for w in kws["core"] if not coverage_map.get(("core", w))]
            rep.err("COVER_CORE", "关键词覆盖",
                    "核心词未 100%% 覆盖，缺：%s" % ", ".join(miss))

    lt = rate("long_tail")
    if lt:
        pct = lt[0] * 100.0 / lt[1]
        rep.metric("长尾词覆盖率", "%.0f%%" % pct, ">=80%", pct >= 80)
        if pct < 80:
            miss = [w for w in kws["long_tail"] if not coverage_map.get(("long_tail", w))]
            rep.err("COVER_LT", "关键词覆盖",
                    "长尾词覆盖率 %.0f%% 低于 80%%，未覆盖：%s" % (pct, ", ".join(miss)))

    for cat in ("attribute", "scenario", "audience", "synonym", "alternative"):
        r = rate(cat)
        if r and r[0] == 0:
            rep.warn("COVER_ZERO", "关键词覆盖",
                     "%s 全部未落地，考虑删除或补进文案" % CATEGORY_LABEL.get(cat, cat))

    # 跨模块冲突：Title vs Item Highlights、Item Highlights vs Search Terms
    # 五点重复只认「同一个词被主攻两次」：长尾词里包含核心词属正常，不报警
    bullet_map = {}
    for (cat, kw), hits in coverage_map.items():
        bs = {h for h in hits if h.startswith("五点")}
        if bs:
            bullet_map[norm(kw)] = bs

    for cat, words in kws.items():
        for kw in words or []:
            hits = coverage_map.get((cat, kw)) or []
            if "Title" in hits and "Item Highlights" in hits:
                rep.err("DUP_TITLE_IH", "关键词分配",
                        "「%s」同时出现在 Title 与 Item Highlights" % kw)
            if "Item Highlights" in hits and "Search Terms" in hits:
                rep.err("DUP_IH_ST", "关键词分配",
                        "「%s」同时出现在 Item Highlights 与 Search Terms" % kw)
            k = norm(kw)
            bs = bullet_map.get(k, set())
            if len(bs) > 1:
                # 某条卖点里如果这个词只是更长关键词的一部分，就不算"独立主攻"
                def explained(b):
                    return any(
                        other != k
                        and (" " + k + " ") in (" " + other + " ")
                        and b in bullet_map[other]
                        for other in bullet_map
                    )
                remaining = {b for b in bs if not explained(b)}
                if len(remaining) > 1:
                    rep.warn("DUP_BULLET", "关键词分配",
                             "「%s」在 %s 重复出现，五点不应重复主攻同一关键词"
                             % (kw, "、".join(sorted(remaining))))


def check_allocation(data, listing, rep):
    alloc = data.get("allocation") or {}
    if not alloc:
        return
    parts = collect_text(listing)
    module_text = {
        "Title": norm(parts.get("Title", "")),
        "Item Highlights": norm(parts.get("Item Highlights", "")),
        "五点": " ".join(norm(b or "") for b in (listing.get("bullets") or [])),
        "描述": norm(parts.get("描述", "")),
        "Search Terms": norm(parts.get("Search Terms", "")),
    }
    seen = {}
    for mod_raw, words in alloc.items():
        mod = MODULE_ALIAS.get(str(mod_raw).strip().lower(), str(mod_raw).strip())
        if mod not in module_text:
            rep.warn("ALLOC_MODULE", "关键词分配", "未知模块「%s」，已跳过" % mod_raw)
            continue
        for kw in words or []:
            k = norm(kw)
            if not k:
                continue
            seen.setdefault(k, []).append(mod)
            if not has_phrase(module_text[mod], k):
                rep.err("ALLOC_MISSING", "关键词分配",
                        "「%s」标注分配给 %s，但该模块正文中找不到" % (kw, mod))
    for k, mods in seen.items():
        if len(mods) > 1:
            rep.warn("ALLOC_MULTI", "关键词分配",
                     "「%s」被分配到多个位置：%s（一个词只主攻一个位置）"
                     % (k, "、".join(mods)))
    # Title ↔ Item Highlights 互斥
    for k, mods in seen.items():
        if "Title" in mods and "Item Highlights" in mods:
            rep.err("ALLOC_CONFLICT", "关键词分配",
                    "「%s」同时分配给 Title 与 Item Highlights" % k)


# ---------------------------------------------------------------- 输出


def render(data, rep):
    out = []
    site = data.get("site") or "-"
    out.append("=" * 66)
    out.append("Amazon Listing 校验报告    站点: %s" % site)
    out.append("=" * 66)

    if rep.metrics:
        out.append("\n[硬指标]（OK=达标, !=未达标；是否阻断见下方问题清单）")
        for name, val, limit, ok in rep.metrics:
            mark = " " if ok is None else ("OK " if ok else "!! ")
            lim = "" if limit in (None, "") else "  (限 %s)" % limit
            out.append("  %s%-22s %s%s" % (mark, name, val, lim))

    if rep.coverage:
        out.append("\n[关键词覆盖]")
        for cat, kw, hits in rep.coverage:
            where = " / ".join(hits) if hits else "未落地"
            out.append("  %-6s %-38s %s" % (cat, kw[:38], where))

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    if rep.issues:
        out.append("\n[问题清单]")
        for level, code, mod, msg in sorted(rep.issues, key=lambda x: order[x[0]]):
            out.append("  [%s] %-16s %-14s %s" % (level, code, mod, msg))
    else:
        out.append("\n[问题清单]\n  无")

    e, w = rep.counts()
    out.append("\n" + "-" * 66)
    out.append("ERROR %d  |  WARN %d" % (e, w))
    out.append("RESULT: %s" % ("PASS" if e == 0 else "FAIL"))
    out.append("-" * 66)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Amazon Listing 硬指标校验")
    ap.add_argument("input", help="listing JSON 文件路径")
    ap.add_argument("--json-report", help="额外输出机器可读报告")
    args = ap.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        sys.stderr.write("读取输入失败: %s\n" % e)
        return 2

    listing = data.get("listing") or {}
    if not listing:
        sys.stderr.write("输入中缺少 listing 字段\n")
        return 2

    rep = Report()
    check_hard_metrics(data, rep)
    check_html(listing, rep)
    check_titlecase(listing.get("title", ""), "Title", rep)
    check_titlecase(listing.get("item_highlights", ""), "Item Highlights", rep)
    check_forbidden(data, listing, rep)
    check_keywords(data, listing, rep)
    check_allocation(data, listing, rep)

    print(render(data, rep))

    if args.json_report:
        payload = {
            "site": data.get("site"),
            "metrics": [
                {"name": n, "value": v, "limit": l, "pass": o}
                for n, v, l, o in rep.metrics
            ],
            "coverage": [
                {"category": c, "keyword": k, "modules": h}
                for c, k, h in rep.coverage
            ],
            "issues": [
                {"level": lv, "code": c, "module": m, "message": msg}
                for lv, c, m, msg in rep.issues
            ],
            "errors": rep.counts()[0],
            "warnings": rep.counts()[1],
            "result": "PASS" if rep.counts()[0] == 0 else "FAIL",
        }
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("JSON 报告: %s" % args.json_report)

    return 0 if rep.counts()[0] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
