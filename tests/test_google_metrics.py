import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

class TestBuildReport(unittest.TestCase):
    def _period(self, cost, clicks, conversions, impressions):
        return {
            "cost_clp": cost, "clicks": clicks, "conversions": conversions,
            "impressions": impressions,
            "ctr_pct": clicks / impressions * 100 if impressions else 0,
            "cvr_pct": conversions / clicks * 100 if clicks else 0,
            "cpa_clp": cost / conversions if conversions else None,
            "cpc_clp": cost / clicks if clicks else None,
        }

    def test_build_report_contains_key_metrics(self):
        import google_metrics as gm
        last7  = self._period(50000, 200, 15, 2000)
        last30 = self._period(180000, 800, 55, 8000)
        devices = {
            "DESKTOP": {"clicks": 200, "conversions": 22.0, "cost_clp": 50000, "cvr_pct": 11.0, "cpa_clp": 2273},
            "MOBILE":  {"clicks": 600, "conversions": 33.0, "cost_clp": 130000, "cvr_pct": 5.5, "cpa_clp": 3939},
        }
        schedule = {
            "MONDAY":   {"clicks": 120, "conversions": 10.0, "cost_clp": 30000, "cvr_pct": 8.3, "cpa_clp": 3000},
            "SATURDAY": {"clicks": 40,  "conversions": 1.0,  "cost_clp": 20000, "cvr_pct": 2.5, "cpa_clp": 20000},
        }
        report = gm.build_report("2026-05-23", last7, last30, devices, schedule)
        self.assertIn("Reporte", report)
        self.assertIn("50,000", report)
        self.assertIn("DESKTOP", report)
        self.assertIn("SATURDAY", report)

    def test_cpa_none_shows_na(self):
        import google_metrics as gm
        p = {"cost_clp": 0, "clicks": 0, "conversions": 0, "impressions": 0,
             "ctr_pct": 0, "cvr_pct": 0, "cpa_clp": None, "cpc_clp": None}
        report = gm.build_report("2026-05-23", p, p, {}, {})
        self.assertIn("N/A", report)

if __name__ == "__main__":
    unittest.main()
