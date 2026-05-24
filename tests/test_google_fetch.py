import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

ENV_CONTENT = """
export GOOGLE_ADS_DEVELOPER_TOKEN="test-token"
export GOOGLE_ADS_CLIENT_ID="test-client-id"
export GOOGLE_ADS_CLIENT_SECRET="test-secret"
export GOOGLE_ADS_REFRESH_TOKEN="test-refresh"
export GOOGLE_ADS_LOGIN_CUSTOMER_ID="7852722044"
export GOOGLE_ADS_CUSTOMER_ID="2868354693"
"""

class TestLoadEnv(unittest.TestCase):
    @patch("pathlib.Path.read_text", return_value=ENV_CONTENT)
    def test_load_env_returns_all_keys(self, _mock):
        import google_fetch as gf
        config = gf._load_env()
        self.assertEqual(config["developer_token"], "test-token")
        self.assertEqual(config["client_id"], "test-client-id")
        self.assertEqual(config["login_customer_id"], "7852722044")

class TestGetCampaigns(unittest.TestCase):
    def _make_row(self, name, cost_micros, clicks, impressions, conversions):
        row = MagicMock()
        row.campaign.id = 1
        row.campaign.name = name
        row.campaign.status.name = "ENABLED"
        row.campaign.bidding_strategy_type.name = "MAXIMIZE_CONVERSIONS"
        row.campaign.advertising_channel_type.name = "SEARCH"
        row.metrics.impressions = impressions
        row.metrics.clicks = clicks
        row.metrics.conversions = conversions
        row.metrics.cost_micros = cost_micros
        row.metrics.ctr = clicks / impressions if impressions else 0
        row.metrics.average_cpc = cost_micros / clicks if clicks else 0
        row.metrics.conversion_rate = conversions / clicks if clicks else 0
        row.metrics.search_impression_share = 0.72
        row.metrics.search_budget_lost_impression_share = 0.28
        return row

    @patch("builtins.open", mock_open(read_data=ENV_CONTENT))
    def test_get_campaigns_converts_micros(self):
        import google_fetch as gf
        mock_client = MagicMock()
        row = self._make_row("Campana Test", 10_000_000_000, 100, 1000, 7.0)
        mock_client.get_service.return_value.search.return_value = [row]
        mock_client.get_type.return_value = MagicMock()
        campaigns = gf.get_campaigns(mock_client)
        self.assertEqual(len(campaigns), 1)
        self.assertAlmostEqual(campaigns[0]["cost_clp"], 10000.0)
        self.assertEqual(campaigns[0]["name"], "Campana Test")

class TestGetKeywords(unittest.TestCase):
    def _make_kw_row(self, text, match, qs, cost_micros, conversions):
        row = MagicMock()
        row.ad_group_criterion.keyword.text = text
        row.ad_group_criterion.keyword.match_type.name = match
        row.ad_group_criterion.status.name = "ENABLED"
        row.ad_group_criterion.quality_info.quality_score = qs
        row.campaign.name = "Test Campaign"
        row.ad_group.name = "Test AdGroup"
        row.metrics.impressions = 100
        row.metrics.clicks = 10
        row.metrics.conversions = conversions
        row.metrics.cost_micros = cost_micros
        return row

    @patch("builtins.open", mock_open(read_data=ENV_CONTENT))
    def test_get_keywords_flags_low_qs(self):
        import google_fetch as gf
        mock_client = MagicMock()
        rows = [
            self._make_kw_row("impermeabilizacion", "BROAD", 8, 5_000_000_000, 3.0),
            self._make_kw_row("trongemen", "BROAD", 1, 500_000_000, 0.0),
        ]
        mock_client.get_service.return_value.search.return_value = rows
        mock_client.get_type.return_value = MagicMock()
        keywords = gf.get_keywords(mock_client)
        low_qs = [k for k in keywords if k["qs"] is not None and k["qs"] < 5]
        self.assertEqual(len(low_qs), 1)
        self.assertEqual(low_qs[0]["text"], "trongemen")

if __name__ == "__main__":
    unittest.main()
