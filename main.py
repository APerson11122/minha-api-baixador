from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

# Permite que a tua extensão do Chrome fale com a API sem erros de CORS
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
    return {"status": "API Online", "msg": "Baixador Ultra HD funcionando!"}

@app.post("/api/get-download-link")
def get_download_link(data: RequestData):
    url = data.url
    formato_selecionado = data.format

    # Configurar os formatos do yt-dlp
    # NOTA: O YouTube separa áudio e vídeo em resoluções altas. 
    # Para sacar direto via link no browser, pedimos a melhor qualidade que já venha com áudio/vídeo juntos (normalmente 720p/1080p).
    # Se for MP3, extraímos apenas o fluxo de áudio direto.
    if formato_selecionado.startswith("mp3"):
        ydl_format = "bestaudio/best"
    elif "8k" in formato_selecionado:
        ydl_format = "bestvideo[height<=4320]+bestaudio/best"
    elif "4k" in formato_selecionado:
        ydl_format = "bestvideo[height<=2160]+bestaudio/best"
    else:
        ydl_format = "best"

    try:
        # Comando para extrair as informações do vídeo em formato JSON, sem descarregar no servidor
        process = subprocess.Popen(
            ["yt-dlp", "-j", "-f", ydl_format, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise Exception(stderr)

        video_info = json.loads(stdout)
        
        # Retorna o link direto do servidor da plataforma (Google, TikTok, etc.)
        return {
            "status": "success",
            "download_url": video_info.get("url"),
            "title": video_info.get("title", "video_extensao")
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar link: {str(e)}")
