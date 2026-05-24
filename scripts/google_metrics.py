"""Reporte semanal de metricas Google Ads con comparacion de periodos."""
from datetime import datetime
from pathlib import Path
import google_fetch as gf

OUTPUT_DIR = Path(r"C:\Users\gvera\andes-claude")
DAY_ORDER  = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

def _aggregate(client, days):
    rows = gf.run_query(client, gf.CUSTOMER_ID, f"""
        SELECT metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status != 'REMOVED'
    """)
    t = {"impressions": 0, "clicks": 0, "conversions": 0.0, "cost_clp": 0.0}
    for r in rows:
        t["impressions"] += r.metrics.impressions
        t["clicks"]      += r.metrics.clicks
        t["conversions"] += r.metrics.conversions
        t["cost_clp"]    += r.metrics.cost_micros / 1_000_000
    t["ctr_pct"] = (t["clicks"] / t["impressions"] * 100) if t["impressions"] > 0 else 0.0
    t["cvr_pct"] = (t["conversions"] / t["clicks"] * 100) if t["clicks"] > 0 else 0.0
    t["cpa_clp"] = (t["cost_clp"] / t["conversions"]) if t["conversions"] > 0 else None
    t["cpc_clp"] = (t["cost_clp"] / t["clicks"]) if t["clicks"] > 0 else None
    return t

def build_report(date_str, last7, last30, devices, schedule):
    def fmt_cpa(d):
        return f"CLP {d['cpa_clp']:,.0f}" if d.get("cpa_clp") else "N/A"
    def fmt_cpc(d):
        return f"CLP {d['cpc_clp']:,.0f}" if d.get("cpc_clp") else "N/A"

    lines = [
        f"# Reporte de Metricas Google Ads — {date_str}",
        f"**Cuenta:** Andes Construccion | Customer: {gf.CUSTOMER_ID}",
        "",
        "## Ultimos 7 dias",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Gasto        | CLP {last7['cost_clp']:,.0f} |",
        f"| Clicks       | {last7['clicks']:,} |",
        f"| Conversiones | {last7['conversions']:.1f} |",
        f"| CTR          | {last7['ctr_pct']:.2f}% |",
        f"| CVR          | {last7['cvr_pct']:.2f}% |",
        f"| CPA          | {fmt_cpa(last7)} |",
        f"| CPC          | {fmt_cpc(last7)} |",
        "",
        "## Ultimos 30 dias",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Gasto        | CLP {last30['cost_clp']:,.0f} |",
        f"| Clicks       | {last30['clicks']:,} |",
        f"| Conversiones | {last30['conversions']:.1f} |",
        f"| CTR          | {last30['ctr_pct']:.2f}% |",
        f"| CVR          | {last30['cvr_pct']:.2f}% |",
        f"| CPA          | {fmt_cpa(last30)} |",
        f"| CPC          | {fmt_cpc(last30)} |",
        "",
        "## Performance por Dispositivo (30 dias)",
        "| Dispositivo | Clicks | Conv | CVR | CPA |",
        "|-------------|--------|------|-----|-----|",
    ]
    for device, d in sorted(devices.items(), key=lambda x: -x[1]["clicks"]):
        lines.append(f"| {device} | {d['clicks']:,} | {d['conversions']:.1f} | {d['cvr_pct']:.1f}% | {fmt_cpa(d)} |")

    lines += ["", "## Performance por Dia (30 dias)", "| Dia | Clicks | Conv | CVR | CPA |", "|-----|--------|------|-----|-----|"]
    for day in DAY_ORDER:
        if day in schedule:
            d = schedule[day]
            lines.append(f"| {day} | {d['clicks']:,} | {d['conversions']:.1f} | {d['cvr_pct']:.1f}% | {fmt_cpa(d)} |")

    return "\n".join(lines)

def run():
    client   = gf.init_client()
    today    = datetime.now().strftime("%Y-%m-%d")
    print("Obteniendo metricas...")
    last7    = _aggregate(client, 7)
    last30   = _aggregate(client, 30)
    devices  = gf.get_device_perf(client, days=30)
    schedule = gf.get_schedule_perf(client, days=30)
    report   = build_report(today, last7, last30, devices, schedule)
    out      = OUTPUT_DIR / f"google-metrics-{today}.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nGuardado: {out}")

if __name__ == "__main__":
    run()
