"""Monitor de search terms — detecta irrelevantes y sugiere negativos."""
from datetime import datetime
from pathlib import Path
import google_fetch as gf

OUTPUT_DIR = Path(r"C:\Users\gvera\andes-claude")

DIY_SIGNALS        = ["comprar", "precio", "oferta", "tienda", "producto", "rollo", "litro",
                      "kg", "gramo", "ferreteria", "sodimac", "easy", "maestro"]
RETAIL_SIGNALS     = ["membrana asfaltica", "pintura impermeabilizante precio",
                      "membrana asfaltica comprar", "material impermeabilizacion"]
ENGLISH_SIGNALS    = ["waterproof", "roofing", "contractor", "repair", "leak", "water damage"]
BRAND_SIGNALS      = ["andes construccion", "andesconstruccion"]
IRRELEVANT_SIGNALS = ["casa", "habitacion", "bricolag", "diy", "tutorial", "como hacer",
                      "techo vegetal", "jardin", "decoracion"]

def classify_terms(terms):
    classified = []
    for t in terms:
        term_lower = t["term"].lower()
        cat = "RELEVANT"
        if any(s in term_lower for s in DIY_SIGNALS):
            cat = "DIY_PRODUCT"
        elif any(s in term_lower for s in ENGLISH_SIGNALS):
            cat = "ENGLISH"
        elif any(s in term_lower for s in IRRELEVANT_SIGNALS):
            cat = "IRRELEVANT"
        elif any(s in term_lower for s in BRAND_SIGNALS):
            cat = "BRAND"
        classified.append({**t, "category": cat})
    return classified

def suggest_negatives(flagged_terms):
    bad = [t for t in flagged_terms if t["category"] in ("DIY_PRODUCT", "ENGLISH", "IRRELEVANT")]
    seen = set()
    suggestions = []
    for t in sorted(bad, key=lambda x: -x["cost_clp"]):
        for signal in DIY_SIGNALS + RETAIL_SIGNALS + ENGLISH_SIGNALS + IRRELEVANT_SIGNALS:
            if signal in t["term"].lower() and signal not in seen:
                seen.add(signal)
                suggestions.append({
                    "keyword":    signal,
                    "match_type": "BROAD",
                    "reason":     f"Aparece en '{t['term']}' — CLP {t['cost_clp']:,.0f}, 0 conv",
                    "category":   t["category"],
                })
    return suggestions

def run(days=30):
    client = gf.init_client()
    today  = datetime.now().strftime("%Y-%m-%d")
    print(f"Obteniendo search terms (ultimos {days} dias)...")

    raw      = gf.get_search_terms(client, days=days)
    flagged  = classify_terms(raw)
    negatives = suggest_negatives(flagged)

    by_cat = {}
    for t in flagged:
        by_cat.setdefault(t["category"], []).append(t)

    lines = [
        f"# Search Terms Report — {today}",
        f"**Total terminos:** {len(raw)} | **Irrelevantes detectados:** "
        f"{len([t for t in flagged if t['category'] != 'RELEVANT'])}",
        "",
    ]
    for cat in ["DIY_PRODUCT", "ENGLISH", "IRRELEVANT", "BRAND", "RELEVANT"]:
        items = by_cat.get(cat, [])
        if not items:
            continue
        lines += [f"## {cat} ({len(items)} terminos)",
                  "| Termino | Clicks | Conv | Costo |",
                  "|---------|--------|------|-------|"]
        for t in sorted(items, key=lambda x: -x["cost_clp"])[:20]:
            lines.append(f"| {t['term']} | {t['clicks']} | {t['conversions']:.1f} | CLP {t['cost_clp']:,.0f} |")
        lines.append("")

    if negatives:
        lines += ["## Negativos Sugeridos", "Agregar en: Shared Library > Negative keyword lists",
                  "", "| Keyword | Match | Razon |", "|---------|-------|-------|"]
        for n in negatives:
            lines.append(f"| {n['keyword']} | {n['match_type']} | {n['reason']} |")

    report = "\n".join(lines)
    out = OUTPUT_DIR / f"google-search-terms-{today}.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nGuardado: {out}")

if __name__ == "__main__":
    run()
