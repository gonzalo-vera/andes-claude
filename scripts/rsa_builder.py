"""
rsa_builder.py — Agrega RSA #2 a grupos de anuncios que solo tienen 1 RSA activo.

Ángulo de RSA #2: authority + b2b + offer
(diferenciado de RSA #1 que normalmente cubre service + urgency)

Uso:
  python scripts/rsa_builder.py           # dry-run: muestra qué RSAs crearía
  python scripts/rsa_builder.py --apply   # ejecuta en cuenta real
  python scripts/rsa_builder.py --group "Nombre Ad Group"  # solo ese grupo
"""
import sys, io, argparse, json
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from google_fetch import init_client, run_query, get_rsa_performance, get_ad_groups, CUSTOMER_ID

COPY_BANK_PATH = Path("ads/copy_bank.json")

AD_GROUP_URLS = {
    "default": "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "impermeabilizac": "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "membrana":        "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "sello":           "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "techo":           "https://www.andesconstruccion.com/servicios/impermeabilizacion",
    "construccion":    "https://www.andesconstruccion.com/servicios/construccion",
    "remodelac":       "https://www.andesconstruccion.com/servicios/remodelacion",
}

RSA2_PROFILE = "authority_b2b"


def load_copy_bank():
    return json.loads(COPY_BANK_PATH.read_text(encoding="utf-8"))


def get_rsa2_copy(copy_bank, profile_key=RSA2_PROFILE):
    """Selecciona headlines y descriptions del perfil dado, priorizando los pillars correctos."""
    profile  = copy_bank["rsa_profiles"][profile_key]
    pillars  = profile["headline_pillars"]
    d_pillars = profile["description_pillars"]

    # Selecciona headlines ordenados por pillar priority
    headlines = []
    for pillar in pillars:
        for h in copy_bank["headlines"]:
            if h["pillar"] == pillar and h["text"] not in headlines:
                headlines.append(h["text"])

    # Selecciona descriptions ordenadas por pillar priority
    descriptions = []
    for pillar in d_pillars:
        for d in copy_bank["descriptions"]:
            if d["pillar"] == pillar and d["text"] not in descriptions:
                descriptions.append(d["text"])

    # Google RSA: máximo 15 headlines y 4 descriptions
    return headlines[:15], descriptions[:4]


def get_final_url(ad_group_name):
    name_lower = ad_group_name.lower()
    for key, url in AD_GROUP_URLS.items():
        if key in name_lower:
            return url
    return AD_GROUP_URLS["default"]


def find_groups_needing_rsa2(client, target_group=None):
    """
    Retorna lista de ad groups que tienen < 2 RSAs activos.
    Excluye brand campaigns (ad_group.name contiene 'brand').
    """
    rsas = get_rsa_performance(client, days=30)

    rsa_count = {}
    for rsa in rsas:
        ag_name = rsa["ad_group_name"]
        if "brand" in ag_name.lower():
            continue
        if ag_name not in rsa_count:
            rsa_count[ag_name] = {
                "count": 0,
                "campaign_id": rsa["campaign_id"],
                "campaign_name": rsa["campaign_name"],
                "ad_group_id": rsa["ad_group_id"],
            }
        rsa_count[ag_name]["count"] += 1

    needs_rsa2 = []
    for name, info in rsa_count.items():
        if target_group and target_group.lower() not in name.lower():
            continue
        if info["count"] < 2:
            needs_rsa2.append({
                "ad_group_name": name,
                "ad_group_id": info["ad_group_id"],
                "campaign_id": info["campaign_id"],
                "campaign_name": info["campaign_name"],
                "current_rsa_count": info["count"],
            })

    # Si hay grupos sin datos de performance (0 impresiones), buscarlos en get_ad_groups
    if not rsa_count:
        for ag in get_ad_groups(client):
            if "brand" in ag["name"].lower():
                continue
            if target_group and target_group.lower() not in ag["name"].lower():
                continue
            needs_rsa2.append({
                "ad_group_name": ag["name"],
                "ad_group_id": ag["id"],
                "campaign_id": ag["campaign_id"],
                "campaign_name": ag["campaign_name"],
                "current_rsa_count": 0,
            })

    return needs_rsa2


def create_rsa2(client, ag_info, headlines, descriptions, final_url, dry_run=True):
    ag_name = ag_info["ad_group_name"]
    ag_id   = ag_info["ad_group_id"]
    ag_rn   = f"customers/{CUSTOMER_ID}/adGroups/{ag_id}"

    print(f"\n  Ad Group: '{ag_name}' (ID: {ag_id})")
    print(f"  URL: {final_url}")
    print(f"  Headlines ({len(headlines)}):")
    for h in headlines:
        print(f"    [{len(h):2d}] {h}")
    print(f"  Descriptions ({len(descriptions)}):")
    for d in descriptions:
        print(f"    [{len(d):2d}] {d}")

    if dry_run:
        print("  DRY: RSA #2 no creada")
        return

    ada_service = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")
    ad_group_ad = op.create
    ad_group_ad.ad_group = ag_rn
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

    rsa = ad_group_ad.ad.responsive_search_ad
    for text in headlines:
        h = client.get_type("AdTextAsset")
        h.text = text
        rsa.headlines.append(h)
    for text in descriptions:
        d = client.get_type("AdTextAsset")
        d.text = text
        rsa.descriptions.append(d)

    ad_group_ad.ad.final_urls.append(final_url)

    resp = ada_service.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
    print(f"  OK: {resp.results[0].resource_name}")


def run(dry_run=True, target_group=None):
    copy_bank = load_copy_bank()
    client    = init_client()

    header = "=== DRY RUN ===" if dry_run else "=== APLICANDO CAMBIOS ==="
    print(f"\n{header}")
    print(f"Perfil RSA #2: {RSA2_PROFILE}")

    groups = find_groups_needing_rsa2(client, target_group)

    if not groups:
        print("\nTodos los ad groups ya tienen 2+ RSAs activos. Nada que hacer.")
        return

    print(f"\nAd groups que necesitan RSA #2: {len(groups)}")

    headlines, descriptions = get_rsa2_copy(copy_bank, RSA2_PROFILE)

    for ag_info in groups:
        final_url = get_final_url(ag_info["ad_group_name"])
        print(f"\n--- Creando RSA #2 para '{ag_info['ad_group_name']}' (actualmente: {ag_info['current_rsa_count']} RSA) ---")
        create_rsa2(client, ag_info, headlines, descriptions, final_url, dry_run)

    footer = "=== DRY RUN terminado ===" if dry_run else "=== RSAs CREADAS ==="
    print(f"\n{footer}")
    if dry_run:
        print("Correr con --apply para ejecutar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crea RSA #2 en ad groups con una sola variante")
    parser.add_argument("--apply", action="store_true", help="Ejecuta los cambios (sin --apply es dry-run)")
    parser.add_argument("--group", type=str, default=None, help="Filtrar por nombre de ad group")
    args = parser.parse_args()
    run(dry_run=not args.apply, target_group=args.group)
