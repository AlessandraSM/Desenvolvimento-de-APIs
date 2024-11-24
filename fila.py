from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, constr
from typing import List
from datetime import datetime

app = FastAPI()

# Definindo um tipo restrito para o tipo de atendimento
class ClienteEntrada(BaseModel):
    nome: str = Field(..., max_length=20, description="Nome do cliente (máximo de 20 caracteres).")
    tipo_atendimento: constr(pattern="^[NP]$") = Field(..., description="Tipo de atendimento: 'N' (normal) ou 'P' (prioritário).")

# Modelo para representar um cliente na fila
class Cliente(BaseModel):
    posicao: int
    nome: str
    data_chegada: str
    atendido: bool  # Adicionado para refletir o status do atendimento

# Fila de clientes em memória
fila = [
    {"nome": "Alessandra", "data_chegada": "23/11/2024 07:30:00", "atendido": False},
    {"nome": "Matteo", "data_chegada": "23/11/2024 07:45:00", "atendido": False},
    {"nome": "Heloísa", "data_chegada": "23/11/2024 08:00:00", "atendido": False},
]

@app.get("/fila", response_model=List[Cliente])
def get_fila():
    if len(fila) == 0:
        return []

    fila_com_posicao = []
    for i, cliente in enumerate(fila):
        fila_com_posicao.append({
            "posicao": i + 1,
            "nome": cliente["nome"],
            "data_chegada": cliente["data_chegada"],
            "atendido": cliente["atendido"]
        })
    return fila_com_posicao

@app.get("/fila/{id}", response_model=Cliente)
def get_cliente(id: int):
    if id < 1 or id > len(fila):
        raise HTTPException(
            status_code=404, 
            detail=f"Não há cliente na posição {id} da fila."
        )
    
    posicao_lista = id - 1
    cliente_na_fila = fila[posicao_lista]
    
    return Cliente(
        posicao=id, 
        nome=cliente_na_fila["nome"], 
        data_chegada=cliente_na_fila["data_chegada"],
        atendido=cliente_na_fila["atendido"]
    )

@app.post("/fila", response_model=Cliente)
def add_cliente(cliente_entrada: ClienteEntrada):
    # Criar um dicionário com as informações do novo cliente
    novo_cliente = {
        "nome": cliente_entrada.nome,
        "data_chegada": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo_atendimento": cliente_entrada.tipo_atendimento,
        "atendido": False
    }
    
    # Adicionar cliente na fila, considerando o tipo de atendimento
    if cliente_entrada.tipo_atendimento == "P":
        fila.insert(0, novo_cliente)  # Coloca no início para atendimento prioritário
    else:
        fila.append(novo_cliente)  # Coloca no final para atendimento normal
    
    # Encontrar a posição do novo cliente
    posicao = len(fila)  # A posição é simplesmente o tamanho da fila, após adicionar

    # Retorna o novo cliente com sua posição
    return Cliente(
        posicao=posicao,
        nome=novo_cliente["nome"],
        data_chegada=novo_cliente["data_chegada"],
        atendido=novo_cliente["atendido"]
    )

@app.put("/fila", response_model=List[Cliente])
def atualizar_fila():
    if len(fila) == 0:
        return {"detail": "Não há clientes na fila."}
    
    pessoa = fila[0]  # A pessoa na posição 0
    pessoa["atendido"] = True  # Alterando o status para 'True'

    # Remove o primeiro cliente da fila
    cliente_removido = fila.pop(0)

    # Adiciona o campo 'posicao' para os itens restantes
    for i, cliente in enumerate(fila):
        cliente['posicao'] = i + 1

    # Retorna a lista com o campo 'posicao' para cada cliente
    return fila



@app.delete("/fila/{id}")
def delete_cliente(id: int):
    if id < 1 or id > len(fila):  # Verifica se a posição está correta
        raise HTTPException(
            status_code=404, 
            detail=f"Não há cliente na posição {id} da fila."
        )

    # Remove o cliente da posição indicada
    cliente_removido = fila.pop(id - 1)

    # Atualiza as posições dos clientes restantes
    for i, cliente in enumerate(fila):
        cliente["posicao"] = i + 1  # Atualiza a posição de cada cliente

    return {
        "message": f"Cliente {cliente_removido['nome']} removido da fila.",
        "fila_atualizada": [
            {"posicao": i + 1, "nome": cliente["nome"], "data_chegada": cliente["data_chegada"]}
            for i, cliente in enumerate(fila)
        ]
    }
