"""
weekly_rsa_optimizer.py — Análisis semanal de RSA performance.

Clasifica cada RSA como WINNER / NEUTRO / LOSER basado en:
  - CTR (últimos 14d)
  - CVR (últimos 14d)
  - Ad Strength normalizado
  - Mínimo de impresiones para ser estadísticamente significativo

Genera ads/drafts/weekly_YYYY-MM-DD.md con:
  - Tabla de performance completa
  - Winner insights (por qué funciona)
  - Proposed changes (pausas + nuevos RSAs propuestos)
  - Bloque MUTATIONS_JSON parseable por apply_rsa_drafts.py

La generación de copy para LOSERs la hace Claude dentro de la routine semanal
leyendo este output + copy_bank.json. NO llama a la API de Anthropic.

Uso:
  python scripts/weekly_rsa_optimizer.py                    # análisis 14d
  python scripts/weekly_rsa_optimizer.py --days 7           # análisis 7d
  python scripts/weekly_rsa_optimizer.py --output ruta.md   # output custom
"""
import sys, io, argparse, json
from pathlib import Path
from datetime import date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from google_fetch import init_client, get_rsa_performance, CUSTOMER_ID

DRAFTS_DIR    = Path("ads/drafts")
COPY_BANK_PATH = Path("ads/copy_bank.json")

MIN_IMPRESSIONS_FOR_SCORE = 100
LOSER_MIN_IMPRESSIONS     = 200
LOSER_MAX_CVR             = 0.0

AD_GROUP_URLS = {
    "impermeabilizac": "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "membrana":        "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "sello":           "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "techo":           "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "construccion":    "https://www.andesconstruccion.com/servicios/construccion",
    "remodelac":       "https://www.andesconstruccion.com/servicios/remodelacion",
    "default":         "https://www.andesconstruccion.com/servicios/impermeabilizacion",
}

STRENGTH_SCORE = {
    "EXCELLENT": 1.0,
    "GOOD": 0.75,
    "AVERAGE": 0.5,
    "POOR": 0.25,
    "UNSPECIFIED": 0.3,
    "UNKNOWN": 0.3,
}


def get_final_url(ad_group_name):
    name_lower = ad_group_name.lower()
    for key, url in AD_GROUP_URLS.items():
        if key in name_lower:
            return url
    return AD_GROUP_URLS["default"]


def compute_score(rsa, all_rsas):
    """Score compuesto 0-100: CTR (30%) + CVR (50%) + AdStrength (20%)."""
    impr = rsa["impressions"]
    if impr < MIN_IMPRESSIONS_FOR_SCORE:
        return None, "INSUFFICIENT_DATA"

    max_ctr = max((r["ctr_pct"] for r in all_rsas if r["impressions"] >= MIN_IMPRESSIONS_FOR_SCORE), default=1.0)
    max_cvr = max((r["cvr_pct"] for r in all_rsas if r["impressions"] >= MIN_IMPRESSIONS_FOR_SCORE), default=1.0)

    ctr_norm      = rsa["ctr_pct"] / max_ctr if max_ctr > 0 else 0
    cvr_norm      = rsa["cvr_pct"] / max_cvr if max_cvr > 0 else 0
    strength_norm = STRENGTH_SCORE.get(rsa["strength"], 0.3)

    score = (ctr_norm * 0.30 + cvr_norm * 0.50 + strength_norm * 0.20) * 100
    return round(score, 1), None


def classify(rsa, score, all_scores):
    """WINNER / NEUTRO / LOSER / INSUFFICIENT_DATA."""
    if score is None:
        return "INSUFFICIENT_DATA"

    valid_scores = [s for s in all_scores if s is not None]
    if not valid_scores:
        return "INSUFFICIENT_DATA"

    p75 = sorted(valid_scores)[int(len(valid_scores) * 0.75)]
    p25 = sorted(valid_scores)[int(len(valid_scores) * 0.25)]

    is_loser_by_conv = (
        rsa["impressions"] >= LOSER_MIN_IMPRESSIONS
        and rsa["conversions"] <= LOSER_MAX_CVR
    )

    if score >= p75:
        return "WINNER"
    elif score < p25 or is_loser_by_conv:
        return "LOSER"
    else:
        return "NEUTRO"


def extract_winner_insights(winners):
    """Identifica qué pillars / patrones tienen los winners."""
    insights = []
    for w in winners:
        hl_texts = w["headlines"]
        authority = [h for h in hl_texts if any(x in h for x in ["+", "Anos", "Proyectos", "m2", "m²"])]
        urgency   = [h for h in hl_texts if any(x in h for x in ["Lluvia", "Filtrac", "Llamenos", "Proteja"])]
        b2b       = [h for h in hl_texts if any(x in h for x in ["Empresa", "Edificio", "Directorio", "B2B", "Sin Paraliz"])]

        pillar_hits = []
        if authority:
            pillar_hits.append(f"authority ({', '.join(authority[:2])})")
        if b2b:
            pillar_hits.append(f"b2b ({', '.join(b2b[:2])})")
        if urgency:
            pillar_hits.append(f"urgency ({', '.join(urgency[:2])})")

        insights.append({
            "ad_group": w["ad_group_name"],
            "score": w["score"],
            "ctr": w["ctr_pct"],
            "cvr": w["cvr_pct"],
            "winning_pillars": pillar_hits,
            "strength": w["strength"],
        })
    return insights


def load_copy_bank():
    if not COPY_BANK_PATH.exists():
        return None
    return json.loads(COPY_BANK_PATH.read_text(encoding="utf-8"))


def build_proposed_rsa(copy_bank, ad_group_name, winning_insights):
    """
    Construye el RSA propuesto para reemplazar un LOSER.
    Usa copy_bank + pillars de winners como guía.
    El bloque de copy generado por IA va como comentario con placeholder.
    """
    if not copy_bank:
        return [], []

    # Tomar pillars de winners del mismo grupo o los globales
    winner_pillars = []
    for w in winning_insights:
        if w["ad_group"] == ad_group_name:
            winner_pillars.extend(w["winning_pillars"])

    # Priorizar pillars que ganaron, más offer como ancla
    priority_pillars = ["authority", "b2b", "offer"]
    if any("urgency" in p for p in winner_pillars):
        priority_pillars.insert(0, "urgency")

    headlines = []
    for pillar in priority_pillars:
        for h in copy_bank["headlines"]:
            if h["pillar"] == pillar and h["text"] not in headlines:
                headlines.append(h["text"])

    descriptions = []
    for pillar in ["b2b", "authority", "urgency", "service"]:
        for d in copy_bank["descriptions"]:
            if d["pillar"] == pillar and d["text"] not in descriptions:
                descriptions.append(d["text"])

    return headlines[:12], descriptions[:4]


def build_draft(rsas_analyzed, days, copy_bank):
    today       = date.today().isoformat()
    winners     = [r for r in rsas_analyzed if r["label"] == "WINNER"]
    losers      = [r for r in rsas_analyzed if r["label"] == "LOSER"]
    neutros     = [r for r in rsas_analyzed if r["label"] == "NEUTRO"]
    no_data     = [r for r in rsas_analyzed if r["label"] == "INSUFFICIENT_DATA"]

    insights = extract_winner_insights(winners)

    lines = []
    lines.append(f"# RSA Weekly Draft — {today} ({days}d)")
    lines.append("")
    lines.append(f"Generado: {today} | Ventana análisis: últimos {days} días")
    lines.append(f"RSAs analizados: {len(rsas_analyzed)} | Winners: {len(winners)} | Losers: {len(losers)} | Sin datos: {len(no_data)}")
    lines.append("")

    # --- Tabla de performance ---
    lines.append("## Performance Summary")
    lines.append("")
    lines.append("| Ad Group | Ad ID | Impresiones | CTR | Conv | CPA | Strength | Score | Estado |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rsas_analyzed:
        cpa_str   = f"CLP {r['cpa_clp']:,.0f}" if r["cpa_clp"] else "—"
        score_str = f"{r['score']:.0f}" if r["score"] is not None else "N/A"
        lines.append(
            f"| {r['ad_group_name']} | {r['ad_id']} | {r['impressions']:,} "
            f"| {r['ctr_pct']:.1f}% | {r['conversions']:.0f} | {cpa_str} "
            f"| {r['strength']} | {score_str} | **{r['label']}** |"
        )
    lines.append("")

    # --- Winner Insights ---
    if insights:
        lines.append("## Winner Insights")
        lines.append("")
        for w in insights:
            lines.append(f"**{w['ad_group']}** (score {w['score']}, CTR {w['ctr']:.1f}%, CVR {w['cvr']:.1f}%)")
            if w["winning_pillars"]:
                lines.append(f"  Pillars ganadores: {' | '.join(w['winning_pillars'])}")
            lines.append(f"  Ad Strength: {w['strength']}")
            lines.append("")

    # --- Proposed Changes ---
    mutations_pause  = []
    mutations_create = []

    if losers:
        lines.append("## Proposed Changes")
        lines.append("")

        lines.append("### PAUSE (candidatos a pausar)")
        lines.append("")
        for loser in losers:
            reason = (
                f"{days}d: {loser['conversions']:.0f} conv, "
                f"{loser['impressions']:,} impr, CTR {loser['ctr_pct']:.1f}%"
            )
            lines.append(f"- `{loser['resource_name']}` — {loser['ad_group_name']} ({reason})")
            mutations_pause.append({
                "resource_name": loser["resource_name"],
                "reason": reason,
            })
        lines.append("")

        lines.append("### CREATE NEW RSA (reemplazos propuestos)")
        lines.append("")
        lines.append("> **Nota para Claude:** Revisar los headlines abajo.")
        lines.append("> Para cada LOSER, generar 3-5 headlines adicionales en español")
        lines.append("> (máx 25 chars c/u) tomando los pillars de los WINNERs de ese grupo.")
        lines.append("> Agregar al final de la lista antes de correr apply_rsa_drafts.py")
        lines.append("")

        for loser in losers:
            final_url = get_final_url(loser["ad_group_name"])
            proposed_hl, proposed_desc = build_proposed_rsa(copy_bank, loser["ad_group_name"], insights)

            lines.append(f"#### Ad Group: {loser['ad_group_name']}")
            lines.append(f"Final URL: `{final_url}`")
            lines.append("")
            lines.append(f"**Headlines ({len(proposed_hl)}) — agregar variantes IA al final:**")
            for hl in proposed_hl:
                lines.append(f"- `{hl}` [{len(hl)} chars]")
            lines.append("")
            lines.append(f"**Descriptions ({len(proposed_desc)}):**")
            for desc in proposed_desc:
                lines.append(f"- `{desc}` [{len(desc)} chars]")
            lines.append("")

            mutations_create.append({
                "ad_group_resource": f"customers/{CUSTOMER_ID}/adGroups/{loser['ad_group_id']}",
                "ad_group_name": loser["ad_group_name"],
                "final_url": final_url,
                "headlines": proposed_hl,
                "descriptions": proposed_desc,
            })

    # --- Mutations JSON ---
    mutations = {"date": today, "pause": mutations_pause, "create": mutations_create}

    lines.append("---")
    lines.append("")
    lines.append("## Apply Command")
    lines.append("")
    lines.append("Revisar los cambios propuestos arriba. Si estás de acuerdo, ejecutar:")
    lines.append("```bash")
    lines.append(f"python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_{today}.md           # dry-run")
    lines.append(f"python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_{today}.md --apply   # ejecutar")
    lines.append("```")
    lines.append("")
    lines.append("<!-- MUTATIONS_JSON")
    lines.append(json.dumps(mutations, ensure_ascii=False, indent=2))
    lines.append("MUTATIONS_JSON -->")
    lines.append("")

    return "\n".join(lines)


def run(days=14, output_path=None):
    client    = init_client()
    copy_bank = load_copy_bank()

    print(f"Analizando RSA performance ({days}d)...")
    rsas = get_rsa_performance(client, days=days)

    if not rsas:
        print("No se encontraron RSAs activos con datos de performance.")
        return

    print(f"RSAs encontrados: {len(rsas)}")

    # Calcular scores
    all_scores = []
    for rsa in rsas:
        score, _ = compute_score(rsa, rsas)
        all_scores.append(score)

    # Clasificar
    rsas_analyzed = []
    for i, rsa in enumerate(rsas):
        score = all_scores[i]
        label = classify(rsa, score, all_scores)
        rsas_analyzed.append({**rsa, "score": score, "label": label})

    # Mostrar resumen en consola
    for r in rsas_analyzed:
        score_str = f"{r['score']:.0f}" if r['score'] is not None else "N/A"
        print(f"  [{r['label']:20s}] {r['ad_group_name']:30s} | score={score_str:>5} | impr={r['impressions']:>6,} | conv={r['conversions']:>4.0f} | CTR={r['ctr_pct']:.1f}%")

    # Generar draft
    draft_content = build_draft(rsas_analyzed, days, copy_bank)

    if output_path is None:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = DRAFTS_DIR / f"weekly_{date.today().isoformat()}.md"

    Path(output_path).write_text(draft_content, encoding="utf-8")
    print(f"\nDraft guardado: {output_path}")
    print("Revisar el draft, aprobar los cambios, y correr:")
    print(f"  python scripts/apply_rsa_drafts.py --file {output_path} --apply")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análisis semanal de RSA performance")
    parser.add_argument("--days",   type=int, default=14, help="Ventana de análisis en días (default: 14)")
    parser.add_argument("--output", type=str, default=None, help="Ruta del archivo de output (default: ads/drafts/weekly_YYYY-MM-DD.md)")
    args = parser.parse_args()
    run(days=args.days, output_path=args.output)
