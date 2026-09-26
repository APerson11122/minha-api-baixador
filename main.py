from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pytube import YouTube

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
    return {"status": "API Online e Pronta"}

@app.post("/api/get-download-link")
def get_download_link(data: RequestData):
    url = data.url
    formato_selecionado = data.format

    try:
        # Inicializa o motor de extração direta do YouTube
        yt = YouTube(url)
        
        is_audio = "mp3" in formato_selecionado

        if is_audio:
            # Extrai apenas o fluxo de áudio com a melhor qualidade
            stream = yt.streams.get_audio_only()
        else:
            # Tenta encontrar o vídeo com a maior resolução possível que já inclua ÁUDIO e VÍDEO juntos (progressive)
            # Isto garante que o download funcione diretamente no navegador sem precisar de conversão no servidor
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        if stream and stream.url:
            return {
                "status": "success",
                "download_url": stream.url,
                "title": yt.title
            }
        else:
            raise Exception("Não foi possível gerar um fluxo de download para este vídeo.")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
