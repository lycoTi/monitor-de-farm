import json
import time
from datetime import datetime, timedelta
from plyer import notification
import ctypes

# --- 2. Configurar a Identidade do App ---
# Isso ajuda o Windows a entender que não é apenas "Python", mas sim o teu App
# Podes inventar qualquer nome que pareça um ID reverso (empresa.produto.versao)
app_id = 'Monitor de Farm'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

# Listas de memória para evitar spam de notificações
plantas_avisadas = []
objetivos_avisados = []

while True:
    try:
        with open('plantas.json', 'r', encoding='utf-8') as arquivo:
            dados = json.load(arquivo)
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        time.sleep(5)
        continue

    print("\n" + "="*30)
    print(f"Verificando estufa... {datetime.now().strftime('%H:%M:%S')}")

    agora = datetime.now()

    # --- 1. BLOCO DAS PLANTAS ---
    for slot in dados["slots"]:
        if slot['status'] == "crescendo":
            # Conversão e Cálculos
            formato = "%Y-%m-%d %H:%M:%S"
            inicio = datetime.strptime(slot["horario_plantio"], formato)
            
            duracao = timedelta(minutes=slot["tempo_total_minutos"])
            horario_final = inicio + duracao

            if slot["regada"]:
                regada = duracao * 0.05
                horario_final = horario_final - regada
            
            # Verificação
            if agora >= horario_final:
                print(f"A planta {slot['planta']} está pronta! 🌱")

                if slot['planta'] not in plantas_avisadas:
                    notification.notify(
                        title=f"Colheita Pronta: {slot['planta']}",
                        message="Sua planta cresceu! Corre lá para colher.",
                        app_name="Monitor de Farm",
                        app_icon="icone.ico", # <--- Adiciona esta linha (tem de ter o arquivo na pasta!)
                        timeout=10 
                    )
                    plantas_avisadas.append(slot['planta'])
            else:
                # SE entrou aqui, a planta NÃO está pronta.
                # Removemos da lista de avisados para permitir novo aviso no futuro
                if slot['planta'] in plantas_avisadas:
                    plantas_avisadas.remove(slot['planta'])

                # Cálculo visual do tempo
                tempo_restante = horario_final - agora
                segundos_totais = int(tempo_restante.total_seconds())
                horas = segundos_totais // 3600
                minutos = (segundos_totais % 3600) // 60
                print(f"A planta {slot['planta']} em {horas}h {minutos}m")
            
    # --- 2. BLOCO DOS OBJETIVOS (CRAFTING) ---
    print("\n--- 🛒 Lista de Compras (Objetivos) ---")
    
    for objetivo in dados['objetivos']:
        print(f"Item desejado: {objetivo['nome_item']}")
        
        # Vamos assumir que está tudo pronto, e tentar provar o contrário
        pode_craftar = True 
        
        for ingrediente in objetivo['ingredientes']:
            faltam = ingrediente['alvo'] - ingrediente['atual']
            
            if faltam > 0:
                print(f"  - Faltam {faltam}x {ingrediente['item']}")
                pode_craftar = False # Se falta um, não dá pra craftar o item principal
            else:
                print(f"  - {ingrediente['item']} concluído! ✅")

        # Se depois de olhar todos os ingredientes, 'pode_craftar' ainda for True:
        if pode_craftar:
            print(f"  >>> {objetivo['nome_item']} PODE SER CRIADO! ⭐")
            
            # Notificação de Crafting (Nova Funcionalidade)
            if objetivo['nome_item'] not in objetivos_avisados:
                notification.notify(
                    title=f"Crafting Disponível! ⚒️",
                    message=f"Você já tem tudo para criar: {objetivo['nome_item']}",
                    app_name="Monitor de Farm",
                    app_icon="icone.ico", # <--- Adiciona esta linha (tem de ter o arquivo na pasta!)
                    timeout=10
                )
                objetivos_avisados.append(objetivo['nome_item'])
        else:
            # Se não pode craftar, removemos da lista de avisados (caso você gaste os itens)
            if objetivo['nome_item'] in objetivos_avisados:
                objetivos_avisados.remove(objetivo['nome_item'])

    print("Checagem concluída... dormindo 10s")
    time.sleep(10)