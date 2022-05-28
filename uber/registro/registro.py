import asyncio
from dataclasses import dataclass
from itertools import zip_longest
from typing import List




@dataclass()
class Registro:
    data_pedido: str
    valor_corrida: str
    municipio_corrida: str
    metodo_pagamento: str
    categoria_viagem: str
    corrida_cancelada: bool
    nome_motorista: str
    local_partida: str
    horario_partida: str
    local_chegada: str
    horario_chegada:str
    link: str
    
    @staticmethod
    async def __completo(dados: List):
        metodos = getattr(Registro, '__annotations__')
        if 'Sua viagem' in dados[3]:
            dados.insert(3, None)
        dados.insert(5, False)      
        dados.insert(6, " ")      
        for reg, dado in zip(metodos, dados):
            async with asyncio.Lock():
                if reg == 'categoria_viagem':
                    try:
                        viagem = dado.replace('\xa0', ' ').split(' ')[3]
                        motorista = ' '.join(dado.replace('\xa0', ' ').split(' ')[5:])
                    except IndexError:
                        breakpoint()
                    metodos['categoria_viagem'] = viagem
                    metodos['nome_motorista'] = motorista
                    continue
                if reg == 'nome_motorista':
                    continue
                if dado:
                    metodos[reg] = dado.replace('\xa0', ' ').replace('•••• ', '').strip()
                else:
                    metodos[reg] = dado
        return metodos
        
    @staticmethod
    async def __cancelada(dados: List):
        metodos = getattr(Registro, '__annotations__')
        if 'Sua viagem' in dados[3]:
            dados.insert(3, ' ')
        dados.insert(5, True)
        dados.insert(6, None)
        dados.pop()
        for reg, dado in zip_longest(metodos, dados): 
            async with asyncio.Lock():           
                if reg == 'categoria_viagem':
                    try:
                        viagem =  dado.replace('\xa0', ' ').split(' ')[3]
                        motorista = ' '.join(dado.replace('\xa0', ' ').split(' ')[5:])
                    except IndexError:
                        breakpoint()
                    except AttributeError:
                        breakpoint()
                    metodos['categoria_viagem'] = viagem
                    metodos['nome_motorista'] = motorista
                    continue
                if reg == 'nome_motorista':
                    continue
                if dado and type(dado) != bool:
                    metodos[reg] = dado.replace('\xa0', ' ').replace('Cancelada', "").replace('•••• ', '').strip()
                else:
                    metodos[reg] = dado
        return metodos


    
    @classmethod
    async def to_registro(cls, dado: str):
        dados = dado.split('\n')
        if len(dados) > 7:
            valores = await cls.__completo(dados)
            return cls(**valores)
        else:
            valores = await cls.__cancelada(dados)
            return cls(**valores)
# ['25 February 2022, 8:22pm', 'R$\xa00,00Cancelada', 'Rio de Janeiro', 'Sua viagem no UberX\xa0com Erick', 'Rua Embaú, 561 - Pavuna - Rio de Janeiro - RJ, 21535', 'Informações']