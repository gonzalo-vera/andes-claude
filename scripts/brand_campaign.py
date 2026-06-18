"""
brand_campaign.py — Crea campaña de marca para Andes Construcción.

Crea en orden:
  1. CampaignBudget  (CLP 2,500/día)
  2. Campaign        (Search only, MANUAL_CPC + enhanced CPC, sin Display, sin Search Partners)
  3. AdGroup         (CPC bid CLP 300)
  4. Keywords EXACT  (4 variantes del nombre de marca)
  5. RSA brand       (headlines de marca, descriptions diferenciadores)

Uso:
  python scripts/brand_campaign.py           # dry-run (preview sin cambios)
  python scripts/brand_campaign.py --apply   # ejecuta en cuenta real
"""
import sys, io, argparse, json
from pathlib import Path
from google.protobuf import json_format
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from google_fetch import init_client, CUSTOMER_ID

COPY_BANK_PATH = Path("ads/copy_bank.json")

BRAND_KEYWORDS = [
    "andes construccion",
    "andes construcción",
    "andesconstruccion",
    "andes construccion cl",
]

BASE_URL = "https://www.andesconstruccion.com/"

DAILY_BUDGET_CLP = 2_500
AD_GROUP_CPC_CLP = 300


def load_copy_bank():
    return json.loads(COPY_BANK_PATH.read_text(encoding="utf-8"))


def _get_brand_headlines(copy_bank):
    return [h["text"] for h in copy_bank["brand_headlines"]]


def _get_brand_descriptions(copy_bank):
    return [d["text"] for d in copy_bank["brand_descriptions"]]


def create_budget(client, dry_run=True):
    print("\n[1] Crear budget CLP 2,500/día")
    if dry_run:
        print(f"  DRY: CampaignBudget 'Andes Brand Budget 2026' → {DAILY_BUDGET_CLP:,} CLP/día")
        return "customers/{CUSTOMER_ID}/campaignBudgets/DRY_RUN_ID"

    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")
    budget = op.create
    budget.name = "Andes Brand Budget 2026"
    budget.amount_micros = DAILY_BUDGET_CLP * 1_000_000
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    budget.explicitly_shared = False

    resp = budget_service.mutate_campaign_budgets(customer_id=CUSTOMER_ID, operations=[op])
    rn = resp.results[0].resource_name
    print(f"  OK: {rn}")
    return rn


def create_campaign(client, budget_rn, dry_run=True):
    print("\n[2] Crear campaña 'Andes - Brand 2026'")
    if dry_run:
        print("  DRY: Campaign SEARCH / TARGET_IMPRESSION_SHARE 90% / Search only (sin Display, sin SearchPartners)")
        return f"customers/{CUSTOMER_ID}/campaigns/DRY_RUN_ID"

    campaign_service = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")
    campaign = op.create
    campaign.name = "Andes - Brand 2026"
    campaign.status = client.enums.CampaignStatusEnum.ENABLED
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    campaign.campaign_budget = budget_rn
    # Target Impression Share: ideal para brand — mostrar en 90% de búsquedas de marca
    tis = campaign.target_impression_share
    tis.location = client.enums.TargetImpressionShareLocationEnum.ANYWHERE_ON_PAGE
    tis.location_fraction_micros = 900_000        # 90% impression share objetivo
    tis.cpc_bid_ceiling_micros   = 500_000_000    # CPC máx CLP 500
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = False
    campaign.network_settings.target_content_network = False
    # proto3 optional bool: False == default, no se serializa con proto-plus.
    # json_format.ParseDict sí respeta la presencia explícita de bool false.
    json_format.ParseDict(
        {"containsEuPoliticalAdvertising": False},
        op.create._pb,
        ignore_unknown_fields=True,
    )

    resp = campaign_service.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])
    rn = resp.results[0].resource_name
    print(f"  OK: {rn}")
    return rn


def create_ad_group(client, campaign_rn, dry_run=True):
    print("\n[3] Crear ad group 'Andes Construcción — Brand'")
    if dry_run:
        print(f"  DRY: AdGroup SEARCH_STANDARD, CPC bid {AD_GROUP_CPC_CLP} CLP")
        return f"customers/{CUSTOMER_ID}/adGroups/DRY_RUN_ID"

    ag_service = client.get_service("AdGroupService")
    op = client.get_type("AdGroupOperation")
    ag = op.create
    ag.campaign = campaign_rn
    ag.name = "Andes Construcción — Brand"
    ag.status = client.enums.AdGroupStatusEnum.ENABLED
    ag.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ag.cpc_bid_micros = AD_GROUP_CPC_CLP * 1_000_000

    resp = ag_service.mutate_ad_groups(customer_id=CUSTOMER_ID, operations=[op])
    rn = resp.results[0].resource_name
    print(f"  OK: {rn}")
    return rn


def create_keywords(client, ag_rn, dry_run=True):
    print(f"\n[4] Crear {len(BRAND_KEYWORDS)} keywords EXACT match")
    if dry_run:
        for kw in BRAND_KEYWORDS:
            print(f"  DRY: [EXACT] [{kw}]")
        return

    agc_service = client.get_service("AdGroupCriterionService")
    ops = []
    for kw_text in BRAND_KEYWORDS:
        op = client.get_type("AdGroupCriterionOperation")
        criterion = op.create
        criterion.ad_group = ag_rn
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = kw_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.EXACT
        ops.append(op)

    resp = agc_service.mutate_ad_group_criteria(customer_id=CUSTOMER_ID, operations=ops)
    print(f"  OK: {len(resp.results)} keywords creadas")


def create_brand_rsa(client, ag_rn, copy_bank, dry_run=True):
    headlines    = _get_brand_headlines(copy_bank)
    descriptions = _get_brand_descriptions(copy_bank)

    print(f"\n[5] Crear RSA brand ({len(headlines)} headlines, {len(descriptions)} descriptions)")
    print(f"  Headlines:")
    for h in headlines:
        print(f"    [{len(h):2d}] {h}")
    print(f"  Descriptions:")
    for d in descriptions:
        print(f"    [{len(d):2d}] {d}")
    print(f"  URL: {BASE_URL}")

    if dry_run:
        print("  DRY: RSA brand no creada")
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

    ad_group_ad.ad.final_urls.append(BASE_URL)

    resp = ada_service.mutate_ad_group_ads(customer_id=CUSTOMER_ID, operations=[op])
    print(f"  OK: {resp.results[0].resource_name}")


def run(dry_run=True, existing_budget_rn=None):
    copy_bank = load_copy_bank()
    client    = init_client()

    header = "=== DRY RUN ===" if dry_run else "=== APLICANDO CAMBIOS ==="
    print(f"\n{header}")
    print("Campaña brand: Andes - Brand 2026")
    print(f"Budget: CLP {DAILY_BUDGET_CLP:,}/día | CPC bid: CLP {AD_GROUP_CPC_CLP}")
    print(f"Keywords ({len(BRAND_KEYWORDS)}): {BRAND_KEYWORDS}")

    if existing_budget_rn:
        print(f"\n[1] Reutilizando budget existente: {existing_budget_rn}")
        budget_rn = existing_budget_rn
    else:
        budget_rn = create_budget(client, dry_run)

    campaign_rn = create_campaign(client, budget_rn, dry_run)
    ag_rn       = create_ad_group(client, campaign_rn, dry_run)
    create_keywords(client, ag_rn, dry_run)
    create_brand_rsa(client, ag_rn, copy_bank, dry_run)

    footer = "=== DRY RUN terminado ===" if dry_run else "=== CAMPAÑA CREADA ==="
    print(f"\n{footer}")
    if dry_run:
        print("Revisar preview y correr con --apply para ejecutar.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crea la brand campaign de Andes Construcción")
    parser.add_argument("--apply",          action="store_true", help="Ejecuta los cambios (sin --apply es dry-run)")
    parser.add_argument("--budget-rn",      type=str, default=None, help="Reutilizar un CampaignBudget ya creado (resource_name)")
    args = parser.parse_args()
    run(dry_run=not args.apply, existing_budget_rn=args.budget_rn)
