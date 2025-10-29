from django.test import TestCase
from . import ai_utils

class AIUtilsTests(TestCase):
    def test_summarize_text(self):
        text = "Ceci est un texte de test. Il contient plusieurs phrases. Nous voulons le résumer."
        summary = ai_utils.compute_similarity(text, text)
        self.assertGreater(summary, 0.9)  # Même texte doit avoir similarité > 0.9

    def test_compute_similarity(self):
        text1 = "L'intelligence artificielle est un domaine fascinant."
        text2 = "Le machine learning est une branche de l'IA."
        similarity = ai_utils.compute_similarity(text1, text2)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)