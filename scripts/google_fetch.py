"""Base Google Ads API client — credentials loader + GAQL query runner."""
import re
from pathlib import Path

ENV_FILE    = Path(r"C:\Users\gvera\.claude-ads\.env.google")
CUSTOMER_ID = "2868354693"
MCC_ID      = "7852722044"

def _load_env():
    content = ENV_FILE.read_text(encoding="utf-8")
    def get(key):
        m = re.search(rf'export {key}="([^"]+)"', content)
        if not m:
            raise ValueError(f"Falta {key} en {ENV_FILE}")
        return m.group(1)
    return {
        "developer_token":   get("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id":         get("GOOGLE_ADS_CLIENT_ID"),
        "client_secret":     get("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token":     get("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": get("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus":    True,
    }

def init_client():
    from google.ads.googleads.client import GoogleAdsClient
    return GoogleAdsClient.load_from_dict(_load_env())

def run_query(client, customer_id, gaql):
    service = client.get_service("GoogleAdsService")
    request = client.get_type("SearchGoogleAdsRequest")
    request.customer_id = str(customer_id)
    request.query = gaql
    return list(service.search(request=request))

def get_campaigns(client, days=30):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.bidding_strategy_type, campaign.advertising_channel_type,
               metrics.impressions, metrics.clicks, metrics.conversions,
               metrics.cost_micros, metrics.ctr, metrics.average_cpc,
               metrics.conversion_rate,
               metrics.search_impression_share,
               metrics.search_budget_lost_impression_share
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status != 'REMOVED'
    """)
    result = []
    for r in rows:
        result.append({
            "id":              r.campaign.id,
            "name":            r.campaign.name,
            "status":          r.campaign.status.name,
            "bidding":         r.campaign.bidding_strategy_type.name,
            "channel":         r.campaign.advertising_channel_type.name,
            "impressions":     r.metrics.impressions,
            "clicks":          r.metrics.clicks,
            "conversions":     r.metrics.conversions,
            "cost_clp":        r.metrics.cost_micros / 1_000_000,
            "ctr_pct":         r.metrics.ctr * 100,
            "cpc_clp":         r.metrics.average_cpc / 1_000_000,
            "cvr_pct":         r.metrics.conversion_rate * 100,
            "impression_share":    r.metrics.search_impression_share,
            "lost_budget_pct": r.metrics.search_budget_lost_impression_share,
        })
    return result

def get_keywords(client, days=30):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT campaign.name, ad_group.name,
               ad_group_criterion.keyword.text,
               ad_group_criterion.keyword.match_type,
               ad_group_criterion.status,
               ad_group_criterion.quality_info.quality_score,
               metrics.impressions, metrics.clicks, metrics.conversions,
               metrics.cost_micros
        FROM keyword_view
        WHERE segments.date DURING LAST_{days}_DAYS
          AND ad_group_criterion.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """)
    result = []
    for r in rows:
        qs = r.ad_group_criterion.quality_info.quality_score
        result.append({
            "text":        r.ad_group_criterion.keyword.text,
            "match_type":  r.ad_group_criterion.keyword.match_type.name,
            "status":      r.ad_group_criterion.status.name,
            "qs":          qs if qs != 0 else None,
            "campaign":    r.campaign.name,
            "ad_group":    r.ad_group.name,
            "impressions": r.metrics.impressions,
            "clicks":      r.metrics.clicks,
            "conversions": r.metrics.conversions,
            "cost_clp":    r.metrics.cost_micros / 1_000_000,
        })
    return result

def get_search_terms(client, days=30, min_impressions=5):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT search_term_view.search_term, search_term_view.status,
               campaign.name, ad_group.name,
               metrics.impressions, metrics.clicks, metrics.conversions,
               metrics.cost_micros, metrics.ctr
        FROM search_term_view
        WHERE segments.date DURING LAST_{days}_DAYS
          AND metrics.impressions >= {min_impressions}
        ORDER BY metrics.cost_micros DESC
        LIMIT 500
    """)
    result = []
    for r in rows:
        result.append({
            "term":        r.search_term_view.search_term,
            "status":      r.search_term_view.status.name,
            "campaign":    r.campaign.name,
            "ad_group":    r.ad_group.name,
            "impressions": r.metrics.impressions,
            "clicks":      r.metrics.clicks,
            "conversions": r.metrics.conversions,
            "cost_clp":    r.metrics.cost_micros / 1_000_000,
            "ctr_pct":     r.metrics.ctr * 100,
        })
    return result

def get_conversions(client):
    rows = run_query(client, CUSTOMER_ID, """
        SELECT conversion_action.id, conversion_action.name,
               conversion_action.status, conversion_action.category,
               conversion_action.counting_type, conversion_action.primary_for_goal
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
    """)
    result = []
    for r in rows:
        result.append({
            "id":       r.conversion_action.id,
            "name":     r.conversion_action.name,
            "status":   r.conversion_action.status.name,
            "category": r.conversion_action.category.name,
            "counting": r.conversion_action.counting_type.name,
            "primary":  r.conversion_action.primary_for_goal,
        })
    return result

def get_device_perf(client, days=30):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT segments.device,
               metrics.impressions, metrics.clicks, metrics.conversions,
               metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status != 'REMOVED'
    """)
    result = {}
    for r in rows:
        d = r.segments.device.name
        if d not in result:
            result[d] = {"impressions": 0, "clicks": 0, "conversions": 0.0, "cost_clp": 0.0}
        result[d]["impressions"] += r.metrics.impressions
        result[d]["clicks"]      += r.metrics.clicks
        result[d]["conversions"] += r.metrics.conversions
        result[d]["cost_clp"]    += r.metrics.cost_micros / 1_000_000
    for d in result:
        v = result[d]
        v["cvr_pct"] = (v["conversions"] / v["clicks"] * 100) if v["clicks"] > 0 else 0.0
        v["cpa_clp"] = (v["cost_clp"] / v["conversions"]) if v["conversions"] > 0 else None
    return result

def get_schedule_perf(client, days=30):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT segments.day_of_week,
               metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status != 'REMOVED'
    """)
    result = {}
    for r in rows:
        day = r.segments.day_of_week.name
        if day not in result:
            result[day] = {"impressions": 0, "clicks": 0, "conversions": 0.0, "cost_clp": 0.0}
        result[day]["impressions"] += r.metrics.impressions
        result[day]["clicks"]      += r.metrics.clicks
        result[day]["conversions"] += r.metrics.conversions
        result[day]["cost_clp"]    += r.metrics.cost_micros / 1_000_000
    for day in result:
        v = result[day]
        v["cvr_pct"] = (v["conversions"] / v["clicks"] * 100) if v["clicks"] > 0 else 0.0
        v["cpa_clp"] = (v["cost_clp"] / v["conversions"]) if v["conversions"] > 0 else None
    return result

def get_assets(client):
    rows = run_query(client, CUSTOMER_ID, """
        SELECT asset.id, asset.name, asset.type,
               asset.sitelink_asset.link_text,
               asset.sitelink_asset.description1,
               asset.sitelink_asset.description2,
               asset.final_urls
        FROM asset
        WHERE asset.type IN ('SITELINK', 'CALLOUT', 'STRUCTURED_SNIPPET', 'CALL', 'IMAGE')
    """)
    result = []
    for r in rows:
        t = r.asset.type_.name
        item = {"id": r.asset.id, "name": r.asset.name, "type": t, "urls": list(r.asset.final_urls)}
        if t == "SITELINK":
            item["link_text"] = r.asset.sitelink_asset.link_text
            item["desc1"]     = r.asset.sitelink_asset.description1
            item["desc2"]     = r.asset.sitelink_asset.description2
        result.append(item)
    return result

def get_ads(client, days=30):
    rows = run_query(client, CUSTOMER_ID, f"""
        SELECT ad_group_ad.ad.id, ad_group_ad.ad.type,
               ad_group_ad.ad_strength, ad_group_ad.status,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               campaign.name, ad_group.name,
               metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
        FROM ad_group_ad
        WHERE segments.date DURING LAST_{days}_DAYS
          AND ad_group_ad.status != 'REMOVED'
          AND campaign.status != 'REMOVED'
    """)
    result = []
    for r in rows:
        result.append({
            "id":           r.ad_group_ad.ad.id,
            "type":         r.ad_group_ad.ad.type_.name,
            "strength":     r.ad_group_ad.ad_strength.name,
            "status":       r.ad_group_ad.status.name,
            "campaign":     r.campaign.name,
            "ad_group":     r.ad_group.name,
            "headlines":    len(r.ad_group_ad.ad.responsive_search_ad.headlines),
            "descriptions": len(r.ad_group_ad.ad.responsive_search_ad.descriptions),
            "impressions":  r.metrics.impressions,
            "clicks":       r.metrics.clicks,
            "conversions":  r.metrics.conversions,
            "cost_clp":     r.metrics.cost_micros / 1_000_000,
        })
    return result
