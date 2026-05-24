import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

class TestAuditChecks(unittest.TestCase):
    def test_check_conversions_flags_whatsapp_primary(self):
        import google_audit as ga
        convs = [
            {"name": "whatsapp (1)", "primary": True,  "category": "PAGE_VIEW",        "counting": "ONE_PER_CLICK"},
            {"name": "digitals_formulario", "primary": False, "category": "SUBMIT_LEAD_FORM", "counting": "ONE_PER_CLICK"},
        ]
        results = ga.check_conversions(convs)
        fail_ids = [r["id"] for r in results if r["result"] == "FAIL"]
        self.assertIn("G04", fail_ids)
        self.assertIn("G08", fail_ids)

    def test_check_conversions_passes_when_form_is_primary(self):
        import google_audit as ga
        convs = [
            {"name": "whatsapp (1)",         "primary": False, "category": "PAGE_VIEW",        "counting": "ONE_PER_CLICK"},
            {"name": "digitals_formulario",  "primary": True,  "category": "SUBMIT_LEAD_FORM", "counting": "ONE_PER_CLICK"},
        ]
        results = ga.check_conversions(convs)
        g04 = next(r for r in results if r["id"] == "G04")
        self.assertEqual(g04["result"], "PASS")

    def test_check_keywords_flags_low_qs(self):
        import google_audit as ga
        keywords = [
            {"text": "impermeabilizacion", "qs": 8, "status": "ENABLED", "cost_clp": 5000, "conversions": 3},
            {"text": "trongemen",          "qs": 1, "status": "ENABLED", "cost_clp": 500,  "conversions": 0},
        ]
        results = ga.check_keywords(keywords)
        g28 = next(r for r in results if r["id"] == "G28")
        self.assertEqual(g28["result"], "FAIL")
        self.assertIn("trongemen", g28["detail"])

    def test_check_assets_fails_with_few_sitelinks(self):
        import google_audit as ga
        assets = [
            {"type": "SITELINK", "link_text": "Inicio",   "urls": ["https://andesconstruccion.com"]},
            {"type": "SITELINK", "link_text": "Contacto", "urls": ["https://andesconstruccion.com"]},
            {"type": "CALLOUT",  "name": "20 anos"},
        ]
        results = ga.check_assets(assets)
        g35 = next(r for r in results if r["id"] == "G35")
        self.assertEqual(g35["result"], "FAIL")

    def test_compute_health_score_range(self):
        import google_audit as ga
        checks = {
            "conversion_tracking": [{"result": "PASS"}, {"result": "FAIL"}, {"result": "FAIL"}],
            "wasted_spend":        [{"result": "PASS"}, {"result": "PASS"}],
            "account_structure":   [{"result": "WARNING"}],
            "keywords_qs":        [{"result": "FAIL"}, {"result": "FAIL"}],
            "ads_assets":          [{"result": "PASS"}, {"result": "PASS"}, {"result": "PASS"}],
            "settings":            [{"result": "PASS"}],
        }
        score = ga.compute_health_score(checks)
        self.assertGreaterEqual(score["total"], 0)
        self.assertLessEqual(score["total"], 100)

if __name__ == "__main__":
    unittest.main()
