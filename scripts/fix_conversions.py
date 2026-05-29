"""
fix_conversions.py — Restaura configuración correcta de acciones de conversión.

CAMBIOS QUE HACE:
  1. digitals_formulario → PRIMARY + incluida en metas  (restaura señal GA4 import)
  2. Formulario de Contacto → secondary + NO incluida   (tenía tag sin implementar)
  3. whatsapp (1) → secondary + incluida en AllConv     (señal de respaldo, no bidding)
  4. llamadas anuncios → secondary + NO incluida        (acción muerta, 0 conv)

Corre con: python scripts/fix_conversions.py --dry-run primero
"""
import sys, os, argparse, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))
from google_fetch import _load_env, CUSTOMER_ID

def get_ads_client():
    from google.ads.googleads.client import GoogleAdsClient as _Client
    return _Client.load_from_dict(_load_env())

# Conversion action IDs retrieved via API 2026-05-28
CONVERSION_ACTIONS = {
    "digitals_formulario":   6700480689,   # GA4 import formulario — vuelve a PRIMARY
    "Formulario de Contacto": 6691125040,  # direct tag sin implementar — baja a secondary
    "whatsapp_1":            6691125043,   # WhatsApp click — secondary pero incluida
    "llamadas_anuncios":     6708281452,   # dead action — secondary, no incluida
}

CHANGES = [
    {
        "id":       CONVERSION_ACTIONS["digitals_formulario"],
        "name":     "ANDES CONSTRUCCION (web) digitals_formulario",
        "primary":  True,
        "included": True,
        "reason":   "GA4 import con historico de conversiones — restaurar como primaria",
    },
    {
        "id":       CONVERSION_ACTIONS["Formulario de Contacto"],
        "name":     "Formulario de Contacto",
        "primary":  False,
        "included": False,
        "reason":   "Tag directo sin implementar en GTM — bajar hasta tener AW-ID correcto",
    },
    {
        "id":       CONVERSION_ACTIONS["whatsapp_1"],
        "name":     "whatsapp (1)",
        "primary":  False,
        "included": True,
        "reason":   "Señal de respaldo visible en AllConv; no optimiza bidding directamente",
    },
    {
        "id":       CONVERSION_ACTIONS["llamadas_anuncios"],
        "name":     "llamadas anuncios",
        "primary":  False,
        "included": False,
        "reason":   "Accion muerta (0 conv en 12m) — remover de señal",
    },
]

def run(dry_run=True):
    print(f"\n{'=== DRY RUN ===' if dry_run else '=== APLICANDO CAMBIOS ==='}")
    print(f"Cuenta: {CUSTOMER_ID}\n")

    if dry_run:
        print("Cambios que se aplicarian:\n")
        for c in CHANGES:
            print(f"  [{c['name']}]")
            print(f"    primary_for_goal        → {c['primary']}")
            print(f"    include_in_conversions  → {c['included']}")
            print(f"    Razon: {c['reason']}\n")
        print("Para aplicar: python scripts/fix_conversions.py --apply")
        return

    client = get_ads_client()
    ca_service = client.get_service("ConversionActionService")

    ops = []
    for c in CHANGES:
        resource_name = f"customers/{CUSTOMER_ID}/conversionActions/{c['id']}"
        op = client.get_type("ConversionActionOperation")
        ca = op.update
        ca.resource_name = resource_name
        ca.primary_for_goal = c["primary"]
        op.update_mask.paths.extend(["primary_for_goal"])
        ops.append(op)
        print(f"  Preparado: {c['name']} primary={c['primary']}, included={c['included']}")

    try:
        response = ca_service.mutate_conversion_actions(
            customer_id=CUSTOMER_ID,
            operations=ops
        )
        print(f"\nOK — {len(response.results)} acciones actualizadas:")
        for result in response.results:
            print(f"  {result.resource_name}")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aplicar cambios (sin flag = dry run)")
    args = parser.parse_args()
    run(dry_run=not args.apply)
