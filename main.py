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
    return {"status": "API Online"}

def extrair_id_youtube(url):
    padrao = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    resultado = re.search(padrao, url)
    return resultado.group(1) if resultado else None

@app.post("/api/get-download-link")
def get_download_link(data: RequestData):
    url = data.url
    formato_selecionado = data.format
    
    video_id = extrair_id_youtube(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Apenas links do YouTube são suportados nesta versão estável.")

    try:
        # Usamos o gateway de API do TomP3/Y2Mate que já resolve o áudio e vídeo juntos em alta qualidade
        api_url = "https://tomp3.cc"
        params = urllib.parse.urlencode({'query': url, 'vt': 'home'}).encode('utf-8')
        
        req = urllib.request.Request(api_url, data=params, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        search_data = json.loads(response.read().decode('utf-8'))

        if search_data.get('status') != 'ok':
            raise Exception("Não foi possível mapear os formatos do vídeo.")

        is_audio = formato_selecionado.startsWith("mp3") if hasattr(formato_selecionado, 'startsWith') else "mp3" in formato_selecionado
        key = ""

        if is_audio:
            mp3_group = search_data['links']['mp3']
            key = mp3_group[list(mp3_group.keys())[0]]['k']
        else:
            mp4_group = search_data['links']['mp4']
            # Tenta pegar a maior qualidade disponível (8K -> 4K -> 1080p -> 720p)
            qualidades_alvo = ['4320p', '2160p', '1080p', '720p', '360p']
            for q in qualidades_alvo:
                if q in mp4_group:
                    key = mp4_group[q]['k']
                    break
            if not key:
                key = mp4_group[list(mp4_group.keys())[0]]['k']

        # Converter a chave encontrada no link direto do arquivo final
        convert_url = "https://tomp3.cc"
        convert_params = urllib.parse.urlencode({'vid': search_data['vid'], 'k': key}).encode('utf-8')
        
        req_convert = urllib.request.Request(convert_url, data=convert_params, headers={'User-Agent': 'Mozilla/5.0'})
        response_convert = urllib.request.urlopen(req_convert)
        convert_data = json.loads(response_convert.read().decode('utf-8'))

        if convert_data.get('status') == 'ok' and convert_data.get('dlink'):
            return {
                "status": "success",
                "download_url": convert_data['dlink'],
                "title": search_data.get('title', 'video_extensao')
            }
        else:
            raise Exception("Falha ao gerar link direto.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
