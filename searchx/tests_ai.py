from django.test import TestCase
from . import ai_utils

class AIUtilsTests(TestCase):
   
    def test_compute_similarity(self):
        text1 = "L'intelligence artificielle est un domaine fascinant."
        text2 = "Le machine learning est une branche de l'IA."
        similarity = ai_utils.compute_similarity(text1, text2)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)