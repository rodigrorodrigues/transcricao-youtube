import unittest
import requests
import json
import time
from typing import List, Dict, Any
from typing import List, Dict, Any


class TestTranscricaoAPI(unittest.TestCase):
    BASE_URL = "http://localhost:3000"
    TEST_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo
    
    def setUp(self):
        # Verifica se a API está online antes de cada teste
        try:
            response = requests.get(f"{self.BASE_URL}/ping")
            self.assertEqual(response.status_code, 200)
        except requests.RequestException:
            self.fail("API não está rodando! Execute 'python main.py' primeiro.")

    def test_ping(self):
        """Testa se o endpoint de ping está funcionando"""
        response = requests.get(f"{self.BASE_URL}/ping")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")    def test_transcricao_video_valido(self):
        """Testa transcrição com um vídeo que sabemos que tem legendas"""
        payload = {
            "video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo (primeiro vídeo do YouTube)
        }
        response = requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(isinstance(data["transcricao"], list))
        self.assertTrue(len(data["transcricao"]) > 0)

    def test_transcricao_url_invalida(self):
        """Testa o comportamento com URL inválida"""
        payload = {
            "video_url": "https://www.youtube.com/watch?v=invalid"
        }
        response = requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "erro")
        self.assertTrue(isinstance(data["mensagem"], str))

    def test_transcricao_sem_url(self):
        """Testa o comportamento quando nenhuma URL é fornecida"""
        payload = {}
        response = requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "erro")
        self.assertEqual(data["mensagem"], "URL do vídeo não fornecida")    def test_rate_limit(self):
        """Testa se o rate limit está funcionando"""
        payload = {"video_url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}
        
        # Faz requisições até atingir o limite
        responses = []
        for _ in range(35):  # Tentamos um pouco mais que o limite
            response = requests.post(
                f"{self.BASE_URL}/transcricao",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            responses.append(response.status_code)
            if response.status_code == 429:  # Rate limit atingido
                break
            time.sleep(0.1)  # Pequena pausa entre requisições
        
        # Verifica se encontramos pelo menos uma resposta 429 (rate limit)
        self.assertTrue(
            429 in responses,
            f"Rate limit não atingido. Códigos de resposta: {responses}"
        )
        
        self.fail("Rate limit não está funcionando como esperado")

    def test_cache(self):
        """Testa se o cache está funcionando"""
        payload = {
            "video_url": "https://www.youtube.com/watch?v=BaW_jenozKc"
        }
        
        # Primeira requisição
        start_time = time.time()
        response1 = requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        time1 = time.time() - start_time
        
        # Segunda requisição (deve ser mais rápida por causa do cache)
        start_time = time.time()
        response2 = requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        time2 = time.time() - start_time
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        self.assertTrue(time2 < time1, "Segunda requisição deveria ser mais rápida devido ao cache")

if __name__ == "__main__":
    unittest.main(verbosity=2)
