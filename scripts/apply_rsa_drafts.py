"""
apply_rsa_drafts.py — Aplica mutaciones de un draft semanal aprobado.

Lee el bloque MUTATIONS_JSON del draft y ejecuta:
  - PAUSE: cambia status de RSAs LOSER a PAUSED
  - CREATE: crea nuevos RSAs con el copy propuesto

Uso:
  python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_2026-06-23.md           # dry-run
  python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_2026-06-23.md --apply   # ejecutar
  python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_2026-06-23.md --apply --pause-only
  python scripts/apply_rsa_drafts.py --file ads/drafts/weekly_2026-06-23.md --apply --create-only
"""
import sys, io, argparse, json, re
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from google_fetch import init_client, CUSTOMER_ID

MUTATIONS_PATTERN = re.compile(
    r"<!--\s*MUTATIONS_JSON\s*(.*?)\s*MUTATIONS_JSON\s*-->",
    re.DOTALL,
)


def parse_mutations(draft_path):
    content = Path(draft_path).read_text(encoding="utf-8")
    match = MUTATIONS_PATTERN.search(content)
    if not match:
        raise ValueError(f"No se encontró bloque MUTATIONS_JSON en {draft_path}")
    return json.loads(match.group(1))


def pause_rsas(client, pause_list, dry_run=True):
    if not pause_list:
        print("\n[PAUSE] No hay RSAs para pausar.")
        return

    print(f"\n[PAUSE] RSAs a pausar: {len(pause_list)}")
    if dry_run:
        for item in pause_list:
            print(f"  DRY: PAUSE {item['resource_name']} — {item.get('reason', '')}")
        return

    ada_service = client.get_service("AdGroupAdService")
    ops = []
    for item in pause_list:
        op = client.get_type("AdGroupAdOperation")
        ad_group_ad = op.update
        ad_group_ad.resource_name = item["resource_name"]
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED
        op.update_mask.paths.append("status")
        ops.append(op)

    resp = ada_service.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=ops)
    for r in resp.results:
        print(f"  OK PAUSED: {r.resource_name}")


def create_rsas(client, create_list, dry_run=True):
    if not create_list:
        print("\n[CREATE] No hay RSAs para crear.")
        return

    print(f"\n[CREATE] RSAs a crear: {len(create_list)}")

    ada_service = client.get_service("AdGroupAdService")

    for item in create_list:
        ag_name    = item["ad_group_name"]
        ag_rn      = item["ad_group_resource"]
        final_url  = item["final_url"]
        headlines  = item["headlines"]
        descs      = item["descriptions"]

        print(f"\n  Ad Group: '{ag_name}'")
        print(f"  URL: {final_url}")
        print(f"  Headlines ({len(headlines)}):")
        for h in headlines:
            print(f"    [{len(h):2d}] {h}")
        print(f"  Descriptions ({len(descs)}):")
        for d in descs:
            print(f"    [{len(d):2d}] {d}")

        if dry_run:
            print("  DRY: RSA no creada")
            continue

        op = client.get_type("AdGroupAdOperation")
        ad_group_ad = op.create
        ad_group_ad.ad_group = ag_rn
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

        rsa = ad_group_ad.ad.responsive_search_ad
        for text in headlines:
            h = client.get_type("AdTextAsset")
            h.text = text
            rsa.headlines.append(h)
        for text in descs:
            d = client.get_type("AdTextAsset")
            d.text = text
            rsa.descriptions.append(d)

        ad_group_ad.ad.final_urls.append(final_url)

        resp = ada_service.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
        print(f"  OK CREATED: {resp.results[0].resource_name}")


def stamp_applied(draft_path, dry_run):
    """Agrega timestamp de ejecución al final del draft para historial."""
    if dry_run:
        return
    draft = Path(draft_path)
    content = draft.read_text(encoding="utf-8")
    stamp = f"\n## Applied\nEjecutado: {datetime.now().isoformat(timespec='seconds')} (via apply_rsa_drafts.py --apply)\n"
    if "## Applied" not in content:
        draft.write_text(content + stamp, encoding="utf-8")


def run(draft_path, dry_run=True, pause_only=False, create_only=False):
    mutations = parse_mutations(draft_path)

    header = "=== DRY RUN ===" if dry_run else "=== APLICANDO MUTACIONES ==="
    print(f"\n{header}")
    print(f"Draft: {draft_path}")
    print(f"Fecha draft: {mutations.get('date', 'desconocida')}")
    print(f"Pausas: {len(mutations.get('pause', []))} | Creaciones: {len(mutations.get('create', []))}")

    client = init_client()

    if not create_only:
        pause_rsas(client, mutations.get("pause", []), dry_run)

    if not pause_only:
        create_rsas(client, mutations.get("create", []), dry_run)

    stamp_applied(draft_path, dry_run)

    footer = "=== DRY RUN terminado ===" if dry_run else "=== MUTACIONES APLICADAS ==="
    print(f"\n{footer}")
    if dry_run:
        print("Correr con --apply para ejecutar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aplica mutaciones de un draft semanal aprobado")
    parser.add_argument("--file",        required=True, help="Ruta al archivo de draft (.md)")
    parser.add_argument("--apply",       action="store_true", help="Ejecuta los cambios (sin --apply es dry-run)")
    parser.add_argument("--pause-only",  action="store_true", help="Solo ejecuta las pausas")
    parser.add_argument("--create-only", action="store_true", help="Solo ejecuta las creaciones")
    args = parser.parse_args()
    run(
        draft_path=args.file,
        dry_run=not args.apply,
        pause_only=args.pause_only,
        create_only=args.create_only,
    )
