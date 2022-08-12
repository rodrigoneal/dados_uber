import re
from dataclasses import dataclass
from datetime import datetime


@dataclass(init=False)
class Registro:
    data_pedido: datetime
    valor_corrida: float
    metodo_pagamento: str
    categoria_viagem: str = None
    quilometragem_viagem: float = None
    tempo_viagem: float = None
    nome_motorista: str = None
    local_partida: str
    horario_partida: str
    local_chegada: str
    horario_chegada: str

    @classmethod
    async def to_registro(cls, *, datas: str,
                          rotas, categoria, quilometro: str,
                          tempo: str, pagamento: str, valor: str):
        _class = cls()
        _class.data_pedido, _class.nome_motorista = [
            data.strip() for data in datas.split("com")]
        dados_rota = [rota.strip() for rota in rotas.split("\n") if rota]

        if len(dados_rota) == 5:
            _class.local_partida = dados_rota[1]
            _class.horario_partida = dados_rota[2]
            _class.local_chegada = dados_rota[3]
            _class.horario_chegada = dados_rota[4]

        _class.categoria_viagem = categoria
        _class.quilometragem_viagem = quilometro.replace(" Quilômetros", "").replace(" kilometers", "") if quilometro else None
        _class.tempo_viagem = tempo.replace("\xa0min", "").replace(" min", "") if tempo else None
        _class.metodo_pagamento = pagamento
        _class.valor_corrida = valor.replace("R$\xa0", "").replace(",", ".") if valor else None
        return _class
