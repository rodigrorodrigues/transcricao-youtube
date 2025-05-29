import unittest
import requests
import json
import time
from typing import Dict, Any


class TestTranscricaoAPI(unittest.TestCase):
    BASE_URL = "http://89.116.171.102:9199"
    TEST_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Video com legenda garantida

    def make_request(self, video_url: str) -> requests.Response:
        """Função auxiliar para fazer requisições à API"""
        payload = {"video_url": video_url}
        return requests.post(
            f"{self.BASE_URL}/transcricao",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

    def setUp(self):
        """Verifica se a API está online antes de cada teste"""
        try:
            response = requests.get(f"{self.BASE_URL}/ping")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")
        except requests.RequestException:
            self.fail("❌ API não está rodando! Execute 'python main.py' primeiro.")

    def test_ping(self):
        """Testa se o endpoint de ping está funcionando"""
        response = requests.get(f"{self.BASE_URL}/ping")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["message"], "API operacional")
        print("✅ API está respondendo corretamente")

    def test_transcricao_video_valido(self):
        """Testa transcrição com um vídeo válido"""
        response = self.make_request(self.TEST_VIDEO)
        
        # Se o vídeo não tiver legendas, é aceitável receber 400
        if response.status_code == 400:
            data = response.json()
            self.assertEqual(data["status"], "erro")
            self.assertTrue("legenda" in data["mensagem"].lower())
            print("⚠️ Vídeo não tem legenda disponível (comportamento esperado)")
        else:
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "ok")
            self.assertTrue(isinstance(data["transcricao"], list))
            print("✅ Transcrição obtida com sucesso")

    def test_transcricao_url_invalida(self):
        """Testa o comportamento com URL inválida"""
        response = self.make_request("https://www.youtube.com/watch?v=invalid")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "erro")
        self.assertTrue(isinstance(data["mensagem"], str))
        print("✅ URL inválida tratada corretamente")

    def test_transcricao_sem_url(self):
        """Testa o comportamento quando nenhuma URL é fornecida"""
        response = requests.post(
            f"{self.BASE_URL}/transcricao",
            json={},
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "erro")
        self.assertEqual(data["mensagem"], "URL do vídeo não fornecida")
        print("✅ Requisição sem URL tratada corretamente")

    def test_cache(self):
        """Testa se o cache está funcionando"""
        # Primeira requisição
        start_time = time.time()
        response1 = self.make_request(self.TEST_VIDEO)
        time1 = time.time() - start_time

        if response1.status_code == 200:  # Só testa cache se a primeira requisição funcionou
            # Segunda requisição (deve ser mais rápida por causa do cache)
            start_time = time.time()
            response2 = self.make_request(self.TEST_VIDEO)
            time2 = time.time() - start_time

            self.assertEqual(response2.status_code, 200)
            self.assertTrue(
                time2 < time1,
                f"Segunda requisição não foi mais rápida: {time2:.2f}s > {time1:.2f}s"
            )
            print(f"✅ Cache funcionando (2ª requisição {(time1-time2):.2f}s mais rápida)")


if __name__ == "__main__":
    print("\n🚀 Iniciando testes da API de Transcrição do YouTube...\n")
    unittest.main(verbosity=2)
