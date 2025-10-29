from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from .models import Collection, Concept
import json


class AIEndpointsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create sample concepts and collection
        c1 = Concept.objects.create(name='Pile', description='LIFO')
        c2 = Concept.objects.create(name='File', description='FIFO')
        col = Collection.objects.create(name='col001', description='Collection test')
        col.concepts.set([c1, c2])
        col.resources = ['Ressource 1', 'Ressource 2']
        col.save()

    @patch('searchx.ai_utils.openai.ChatCompletion.create')
    def test_extract_concepts(self, mock_create):
        # Mock OpenAI response
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '["Pile", "File", "Structure de données linéaire"]'
        mock_resp.choices = [mock_choice]
        mock_create.return_value = mock_resp

        body = {"texte": "Les piles et files sont des structures de données linéaires utilisées pour stocker des éléments."}
        resp = self.client.post('/api/ai/extract-concepts/', data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('concepts', data)
        self.assertEqual(data['concepts'][0], 'Pile')

    @patch('searchx.ai_utils.openai.ChatCompletion.create')
    def test_generate_quiz(self, mock_create):
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        # Return a JSON string with quiz
        mock_choice.message.content = '{"quiz": [{"question":"Quelle est la différence entre une pile et une file ?","answer":"Pile=LIFO, File=FIFO"}]}'
        mock_resp.choices = [mock_choice]
        mock_create.return_value = mock_resp

        body = {"collection_id": "col001"}
        resp = self.client.post('/api/ai/generate-quiz/', data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('quiz', data)
        self.assertTrue(len(data['quiz']) >= 1)

    @patch('searchx.ai_utils.openai.ChatCompletion.create')
    def test_ask(self, mock_create):
        mock_resp = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = 'Le tri rapide a une complexité moyenne en O(n log n) et O(n^2) dans le pire cas.'
        mock_resp.choices = [mock_choice]
        mock_create.return_value = mock_resp

        body = {"question": "Quelle est la complexité du tri rapide ?"}
        resp = self.client.post('/api/ai/ask/', data=json.dumps(body), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('answer', data)
        self.assertIn('O(n log n)', data['answer'])
