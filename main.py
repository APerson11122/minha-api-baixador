from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
import urllib.parse
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    url: str
    format: str

@app.get("/")
def home():
    return {"status": "API Ativa"}

def extrair_id(url):
    padrao = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    resultado = re.search(padrao, url)
    return resultado.group(1) if resultado else None

@app.post("/api/get-download-link")
def get_download_link(data: RequestData):
    url = data.url
    formato_selecionado = data.format
    
    video_id = extrair_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Por favor, insira um link válido do YouTube.")

    try:
        # Consulta direta ao motor estável de decodificação de stream
        api_url = "https://tomp3.cc"
        params = urllib.parse.urlencode({'query': url, 'vt': 'home'}).encode('utf-8')
        
        req = urllib.request.Request(
            api_url, 
            data=params, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        )
        response = urllib.request.urlopen(req)
        search_data = json.loads(response.read().decode('utf-8'))

        if search_data.get('status') != 'ok':
            raise Exception("Não foi possível mapear as qualidades do vídeo.")

        is_audio = "mp3" in formato_selecionado
        key = ""

        if is_audio:
            mp3_group = search_data['links']['mp3']
            # Obtém a melhor taxa de bits de áudio disponível
            melhor_audio = list(mp3_group.keys())[0]
            key = mp3_group[melhor_audio]['k']
        else:
            mp4_group = search_data['links']['mp4']
            # Filtra a resolução configurada pela extensão
            resolucoes = ['4320p', '2160p', '1080p', '720p', '360p']
            for res in resolucoes:
                if res in mp4_group:
                    key = mp4_group[res]['k']
                    break
            if not key:
                key = mp4_group[list(mp4_group.keys())][0]['k']

        # Converte o token extraído para o endereço direto do arquivo .mp4/.mp3
        convert_url = "https://tomp3.cc"
        convert_params = urllib.parse.urlencode({'vid': search_data['vid'], 'k': key}).encode('utf-8')
        
        req_convert = urllib.request.Request(
            convert_url, 
            data=convert_params, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        )
        response_convert = urllib.request.urlopen(req_convert)
        convert_data = json.loads(response_convert.read().decode('utf-8'))

        if convert_data.get('status') == 'ok' and convert_data.get('dlink'):
            return {
                "status": "success",
                "download_url": convert_data['dlink'],
                "title": search_data.get('title', 'video_download')
            }
        else:
            raise Exception("O servidor remoto rejeitou a conversão da stream.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
