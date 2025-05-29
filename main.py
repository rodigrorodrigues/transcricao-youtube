import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
import xml.etree.ElementTree as ET
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações da aplicação
app = Flask(__name__)

# Cache simples para resultados
transcript_cache = {}
CACHE_DURATION = timedelta(hours=24)

def cache_transcript(video_id, transcript):
    transcript_cache[video_id] = {
        'data': transcript,
        'timestamp': datetime.now()
    }

def get_cached_transcript(video_id):
    if video_id in transcript_cache:
        cache_entry = transcript_cache[video_id]
        if datetime.now() - cache_entry['timestamp'] < CACHE_DURATION:
            return cache_entry['data']
        del transcript_cache[video_id]
    return None

@app.route("/transcricao", methods=["POST"])
def transcricao():
    try:
        data = request.json
        if not data or 'video_url' not in data:
            return jsonify({
                "status": "erro",
                "mensagem": "URL do vídeo não fornecida"
            }), 400

        video_url = data['video_url']
        video_id = video_url.split("v=")[-1].split("&")[0]

        # Verifica cache primeiro
        cached_result = get_cached_transcript(video_id)
        if cached_result:
            return jsonify({"status": "ok", "transcricao": cached_result})

        # Tenta obter a transcrição via API oficial
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=["pt", "pt-BR", "en"],
                preserve_formatting=True
            )
            linhas = [f"{i+1}. {item['text']}" for i, item in enumerate(transcript) if item['text'].strip()]
            
            # Salva no cache
            cache_transcript(video_id, linhas)
            return jsonify({"status": "ok", "transcricao": linhas})

        except Exception as e:
            logger.warning(f"Erro na API principal para video {video_id}: {str(e)}")
            
            # Fallback para XML direto
            api_url = f"https://video.google.com/timedtext?lang=pt&v={video_id}"
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200 or not response.text.strip():
                raise Exception("Legenda indisponível ou bloqueada")

            root = ET.fromstring(response.text.strip())
            transcript = [{"text": el.text} for el in root.findall("text") if el.text]
            linhas = [f"{i+1}. {item['text']}" for i, item in enumerate(transcript) if item['text'].strip()]
            
            # Salva no cache
            cache_transcript(video_id, linhas)
            return jsonify({"status": "ok", "transcricao": linhas})

    except Exception as e:
        logger.error(f"Erro ao processar requisição: {str(e)}")
        fallback_msg = (
            "❌ Não foi possível acessar a legenda automaticamente.\n\n"
            "🧠 Mesmo que a legenda apareça no vídeo, ela pode estar indisponível para ferramentas externas.\n\n"
            "🔁 Como alternativa:\n"
            "1. Acesse https://downsub.com ou https://yttranscript.com\n"
            "2. Cole o link do vídeo e baixe a legenda.\n"
            "3. Envie aqui o texto da legenda para continuar o processamento.\n\n"
            "📌 Isso garante fidelidade mesmo quando a API está limitada."
        )
        return jsonify({"status": "erro", "mensagem": fallback_msg}), 400

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "/transcricao": "POST - Obter transcrição de vídeo do YouTube",
            "/ping": "GET - Verificar status da API"
        }
    })

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "API operacional"}), 200

@app.route("/test")
def teste_html():
    return send_from_directory(os.getcwd(), "test.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9199))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )