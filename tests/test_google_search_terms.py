import unittest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

class TestClassifyTerms(unittest.TestCase):
    def test_flags_diy_terms(self):
        import google_search_terms as gst
        terms = [
            {"term": "comprar membrana asfaltica", "cost_clp": 5000, "conversions": 0, "clicks": 10},
            {"term": "precio impermeabilizante", "cost_clp": 3000, "conversions": 0, "clicks": 8},
            {"term": "impermeabilizacion edificio santiago", "cost_clp": 8000, "conversions": 2, "clicks": 20},
        ]
        flagged = gst.classify_terms(terms)
        diy = [t for t in flagged if t["category"] == "DIY_PRODUCT"]
        good = [t for t in flagged if t["category"] == "RELEVANT"]
        self.assertEqual(len(diy), 2)
        self.assertEqual(len(good), 1)

    def test_flags_english_terms(self):
        import google_search_terms as gst
        terms = [
            {"term": "waterproofing contractor", "cost_clp": 2000, "conversions": 0, "clicks": 5},
            {"term": "empresa impermeabilizacion", "cost_clp": 4000, "conversions": 1, "clicks": 12},
        ]
        flagged = gst.classify_terms(terms)
        english = [t for t in flagged if t["category"] == "ENGLISH"]
        self.assertEqual(len(english), 1)

    def test_negative_suggestions_deduped(self):
        import google_search_terms as gst
        terms = [
            {"term": "comprar membrana asfaltica precio", "cost_clp": 5000, "conversions": 0, "clicks": 10, "category": "DIY_PRODUCT"},
            {"term": "comprar membrana asfaltica oferta", "cost_clp": 3000, "conversions": 0, "clicks": 7, "category": "DIY_PRODUCT"},
        ]
        suggestions = gst.suggest_negatives(terms)
        kw_texts = [s["keyword"] for s in suggestions]
        self.assertIn("comprar", kw_texts)
        self.assertIn("membrana asfaltica", kw_texts)

if __name__ == "__main__":
    unittest.main()
