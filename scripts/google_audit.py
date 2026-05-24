"""Audit automatizado de Google Ads — genera google-audit-results.json y .md."""
import json
from datetime import datetime
from pathlib import Path
import google_fetch as gf

OUTPUT_DIR   = Path(r"C:\Users\gvera\andes-claude")
WEIGHTS      = {
    "conversion_tracking": 0.25, "wasted_spend": 0.20,
    "account_structure":   0.15, "keywords_qs":  0.15,
    "ads_assets":          0.15, "settings":     0.10,
}
RESULT_SCORE = {"PASS": 1.0, "WARNING": 0.5, "FAIL": 0.0, "N/D": 0.7}

def _check(id_, name, result, detail=""):
    return {"id": id_, "name": name, "result": result, "detail": detail}

def check_conversions(convs):
    primary   = [c for c in convs if c["primary"]]
    checks    = []

    form_primary      = any("formulario" in c["name"].lower() or "form" in c["name"].lower() for c in primary)
    whatsapp_primary  = any("whatsapp" in c["name"].lower() for c in primary)

    if form_primary and not whatsapp_primary:
        checks.append(_check("G04", "Primary conversion = accion valiosa", "PASS"))
        checks.append(_check("G08", "Sin micro-acciones como primary", "PASS"))
    elif whatsapp_primary:
        wp_names = [c["name"] for c in primary if "whatsapp" in c["name"].lower()]
        checks.append(_check("G04", "Primary conversion = accion valiosa", "FAIL",
            f"WhatsApp {wp_names} es PRIMARY — micro-accion. Formulario debe ser PRIMARY."))
        checks.append(_check("G08", "Sin micro-acciones como primary", "FAIL",
            "WhatsApp click != lead B2B. Cambiar a SECONDARY."))
    else:
        primaries_str = ", ".join(c["name"] for c in primary)
        checks.append(_check("G04", "Primary conversion = accion valiosa", "WARNING",
            f"Primary: {primaries_str} — verificar que sean leads reales"))
        checks.append(_check("G08", "Sin micro-acciones como primary", "WARNING",
            "Revisar tipo de conversion"))

    names = [c["name"].lower() for c in convs]
    whatsapp_variants = [n for n in names if "whatsapp" in n]
    if len(whatsapp_variants) >= 2:
        checks.append(_check("G09", "Sin double-counting", "FAIL",
            f"Posible doble conteo WhatsApp: {whatsapp_variants}. Verificar tag nativo vs GA4 import."))
    else:
        checks.append(_check("G09", "Sin double-counting", "PASS"))

    return checks

def check_keywords(keywords):
    checks = []
    qs_vals = [k["qs"] for k in keywords if k["qs"] is not None and k["qs"] > 0]
    avg_qs  = sum(qs_vals) / len(qs_vals) if qs_vals else 0

    if avg_qs >= 7:
        checks.append(_check("G27", "QS promedio >= 7", "PASS", f"QS promedio: {avg_qs:.1f}"))
    elif avg_qs >= 5:
        checks.append(_check("G27", "QS promedio >= 7", "WARNING", f"QS promedio: {avg_qs:.1f}"))
    else:
        checks.append(_check("G27", "QS promedio >= 7", "FAIL", f"QS promedio: {avg_qs:.1f}"))

    low_qs = [k for k in keywords if k["qs"] is not None and k["qs"] < 5 and k["status"] == "ENABLED"]
    if low_qs:
        detail = ", ".join(f"{k['text']} (QS{k['qs']}, CLP{k['cost_clp']:,.0f})" for k in low_qs[:5])
        checks.append(_check("G28", "Keywords QS<5 pausadas", "FAIL", detail))
    else:
        checks.append(_check("G28", "Keywords QS<5 pausadas", "PASS"))

    zero_conv = [k for k in keywords if k["conversions"] == 0 and k["cost_clp"] > 5000]
    if zero_conv:
        detail = ", ".join(f"{k['text']} (CLP{k['cost_clp']:,.0f})" for k in zero_conv[:5])
        checks.append(_check("G12", "Negative keyword coverage adecuada", "WARNING",
            f"Keywords con gasto y 0 conv: {detail}"))
    else:
        checks.append(_check("G12", "Negative keyword coverage adecuada", "PASS"))

    return checks

def check_assets(assets):
    checks    = []
    sitelinks = [a for a in assets if a["type"] == "SITELINK"]
    callouts  = [a for a in assets if a["type"] == "CALLOUT"]

    service_kws = ["impermeabilizacion", "construccion", "remodelacion", "servicios", "cotiz"]
    sitelinks_to_services = [
        s for s in sitelinks
        if any(kw in str(s.get("urls", "")).lower() or kw in s.get("link_text", "").lower()
               for kw in service_kws)
    ]

    if len(sitelinks) >= 4 and len(sitelinks_to_services) >= 3:
        checks.append(_check("G35", "Sitelinks >=4 hacia paginas de servicio", "PASS",
            f"{len(sitelinks)} sitelinks, {len(sitelinks_to_services)} a servicios"))
    elif len(sitelinks) >= 4:
        checks.append(_check("G35", "Sitelinks >=4 hacia paginas de servicio", "WARNING",
            f"{len(sitelinks)} sitelinks pero pocos apuntan a servicios especificos"))
    else:
        checks.append(_check("G35", "Sitelinks >=4 hacia paginas de servicio", "FAIL",
            f"Solo {len(sitelinks)} sitelinks — minimo 4 requeridos"))

    if len(callouts) >= 4:
        checks.append(_check("G36", "Callouts >=4", "PASS", f"{len(callouts)} callouts"))
    elif len(callouts) > 0:
        checks.append(_check("G36", "Callouts >=4", "WARNING", f"Solo {len(callouts)} callouts"))
    else:
        checks.append(_check("G36", "Callouts >=4", "FAIL", "0 callouts"))

    return checks

def check_campaigns(campaigns):
    checks = []
    lost   = max((c["lost_budget_pct"] for c in campaigns), default=0)

    if lost > 0.15:
        checks.append(_check("G30", "Impression share — perdida <15% por presupuesto", "FAIL",
            f"{lost*100:.1f}% impresiones perdidas por budget"))
    elif lost > 0.05:
        checks.append(_check("G30", "Impression share — perdida <15% por presupuesto", "WARNING",
            f"{lost*100:.1f}% impresiones perdidas"))
    else:
        checks.append(_check("G30", "Impression share — perdida <15% por presupuesto", "PASS"))

    if len(campaigns) == 1:
        checks.append(_check("G19", "Estructura de campanas sigue logica de negocio", "WARNING",
            "1 campana hace todo — considerar separar por servicio"))
    else:
        checks.append(_check("G19", "Estructura de campanas sigue logica de negocio", "PASS",
            f"{len(campaigns)} campanas"))

    return checks

def check_device_schedule(devices, schedule):
    checks = []
    desktop_cvr = devices.get("DESKTOP", {}).get("cvr_pct", 0)
    mobile_cvr  = devices.get("MOBILE",  {}).get("cvr_pct", 0)

    if desktop_cvr > 0 and mobile_cvr > 0:
        ratio = desktop_cvr / mobile_cvr if mobile_cvr > 0 else 1
        checks.append(_check("G45", "Bid adjustments por dispositivo activos",
            "PASS" if ratio < 1.5 else "WARNING",
            f"Desktop CVR {desktop_cvr:.1f}% vs Mobile {mobile_cvr:.1f}%"))
    else:
        checks.append(_check("G45", "Bid adjustments por dispositivo activos", "N/D",
            "Sin datos suficientes de dispositivos"))

    sat = schedule.get("SATURDAY", {})
    sat_cpa = sat.get("cpa_clp")
    weekday_cpas = [v["cpa_clp"] for k, v in schedule.items()
                    if k not in ("SATURDAY", "SUNDAY") and v.get("cpa_clp")]
    avg_wday = sum(weekday_cpas) / len(weekday_cpas) if weekday_cpas else None

    if sat_cpa and avg_wday and sat_cpa > avg_wday * 1.5:
        checks.append(_check("G44", "Ad schedule alineado con conversiones", "WARNING",
            f"Sabado CPA {sat_cpa:,.0f} vs weekday avg {avg_wday:,.0f} — considerar ajuste -30%"))
    else:
        checks.append(_check("G44", "Ad schedule alineado con conversiones", "PASS"))

    return checks

def compute_health_score(checks_by_category):
    breakdown = {}
    for cat, weight in WEIGHTS.items():
        cat_checks = checks_by_category.get(cat, [])
        score = round(sum(RESULT_SCORE.get(c["result"], 0.5) for c in cat_checks) /
                      len(cat_checks) * 100) if cat_checks else 70
        breakdown[cat] = {"score": score, "weight": weight, "weighted": round(score * weight, 1)}
    total = round(sum(v["weighted"] for v in breakdown.values()))
    grade = "A" if total >= 85 else "B" if total >= 70 else "C" if total >= 55 else "D" if total >= 40 else "F"
    return {"total": total, "grade": grade, "breakdown": breakdown}

def run():
    client = gf.init_client()
    today  = datetime.now().strftime("%Y-%m-%d")
    print("Corriendo audit Google Ads...")

    convs     = gf.get_conversions(client)
    keywords  = gf.get_keywords(client, days=30)
    campaigns = gf.get_campaigns(client, days=30)
    assets    = gf.get_assets(client)
    devices   = gf.get_device_perf(client, days=30)
    schedule  = gf.get_schedule_perf(client, days=30)

    checks = {
        "conversion_tracking": check_conversions(convs),
        "wasted_spend":        [],
        "account_structure":   check_campaigns(campaigns),
        "keywords_qs":        check_keywords(keywords),
        "ads_assets":          check_assets(assets),
        "settings":            check_device_schedule(devices, schedule),
    }

    health       = compute_health_score(checks)
    total_cost   = sum(c["cost_clp"] for c in campaigns)
    total_conv   = sum(c["conversions"] for c in campaigns)
    total_clicks = sum(c["clicks"] for c in campaigns)

    result = {
        "platform":     "google",
        "account_name": "Andes Construccion",
        "mcc_id":       gf.MCC_ID,
        "customer_id":  gf.CUSTOMER_ID,
        "audit_date":   today,
        "data_source":  "api_direct",
        "health_score": health,
        "kpis_30d": {
            "total_spend_clp": round(total_cost),
            "clicks":          total_clicks,
            "conversions":     round(total_conv, 1),
            "cvr_pct":         round(total_conv / total_clicks * 100, 2) if total_clicks > 0 else 0,
            "cpa_clp":         round(total_cost / total_conv) if total_conv > 0 else None,
        },
        "checks": checks,
    }

    fails    = [c for cat in checks.values() for c in cat if c["result"] == "FAIL"]
    warnings = [c for cat in checks.values() for c in cat if c["result"] == "WARNING"]

    json_out = OUTPUT_DIR / "google-audit-results.json"
    json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    md_lines = [
        f"# Google Ads Audit — {today}",
        f"**Health Score: {health['total']}/100 (Grade {health['grade']})**",
        f"Cuenta: Andes Construccion | Customer: {gf.CUSTOMER_ID}",
        "",
        "## KPIs 30 dias",
        f"- Gasto: CLP {round(total_cost):,}",
        f"- Clicks: {total_clicks:,}",
        f"- Conversiones: {round(total_conv, 1)}",
        f"- CPA: CLP {round(total_cost / total_conv):,}" if total_conv > 0 else "- CPA: N/A",
        "",
        f"## FAILs ({len(fails)})",
    ]
    for c in fails:
        md_lines.append(f"- **[{c['id']}] {c['name']}**: {c['detail']}")
    md_lines += ["", f"## WARNINGs ({len(warnings)})"]
    for c in warnings:
        md_lines.append(f"- **[{c['id']}] {c['name']}**: {c['detail']}")

    md_out = OUTPUT_DIR / "google-audit-results.md"
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Health Score: {health['total']}/100 ({health['grade']})")
    print(f"FAILs: {len(fails)} | WARNINGs: {len(warnings)}")
    print(f"JSON: {json_out}")
    print(f"MD:   {md_out}")

if __name__ == "__main__":
    run()
