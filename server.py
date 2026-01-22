from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from datetime import datetime, timedelta

app = FastAPI()

# Configura onde estão os arquivos HTML
templates = Jinja2Templates(directory="templates")

# Função auxiliar para carregar JSON
def ler_dados():
    try:
        with open('plantas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"slots": [], "objetivos": []}

# Função auxiliar para SALVAR o JSON
def salvar_dados(dados):
    with open('plantas.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Modelo de dados (DTO) para o que vem do Frontend
class PlantarRequest(BaseModel):
    slot_id: int
    nome_planta: str
    tempo_minutos: int

# --- ROTAS (Endereços do site) ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve a página HTML principal"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/dados")
async def get_dados():
    """API que o JavaScript chama para pegar os dados atualizados"""
    dados = ler_dados()
    agora = datetime.now()

    # Vamos pré-calcular o tempo restante aqui no Python para facilitar o JS
    for slot in dados['slots']:
        if slot['status'] == 'crescendo':
            formato = "%Y-%m-%d %H:%M:%S"
            inicio = datetime.strptime(slot["horario_plantio"], formato)
            duracao = timedelta(minutes=slot["tempo_total_minutos"])
            horario_final = inicio + duracao
            
            if slot["regada"]:
                horario_final -= (duracao * 0.05)
            
            tempo_restante = horario_final - agora
            
            if tempo_restante.total_seconds() <= 0:
                slot['status'] = 'pronto' # Atualiza visualmente para o front
                slot['tempo_restante_visual'] = "PRONTO"
            else:
                # Formata bonitinho: 01h 30m
                segundos = int(tempo_restante.total_seconds())
                h = segundos // 3600
                m = (segundos % 3600) // 60
                slot['tempo_restante_visual'] = f"{h}h {m}m"

    return dados

@app.post("/api/plantar")
async def plantar(pedido: PlantarRequest):
    dados = ler_dados()
    
    # Procura o slot correto
    encontrou = False
    for slot in dados['slots']:
        if slot['id'] == pedido.slot_id:
            slot['planta'] = pedido.nome_planta
            slot['status'] = 'crescendo'
            slot['tempo_total_minutos'] = pedido.tempo_minutos
            # Registra o momento exato do clique como inicio
            slot['horario_plantio'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            slot['regada'] = False # Reseta a rega
            encontrou = True
            break
    
    if not encontrou:
        raise HTTPException(status_code=404, detail="Slot não encontrado")
        
    salvar_dados(dados)
    return {"mensagem": "Plantado com sucesso!"}

# Para rodar: uvicorn server:app --reload --host 0.0.0.0