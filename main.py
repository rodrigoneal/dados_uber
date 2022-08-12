import asyncio

import pandas as pd
from dotenv import dotenv_values
from playwright.async_api import async_playwright

from etc import ultima_execucao
from uber.pages.pages import gerar_link, logar, result, get_link, get_dados
from uber_gastos import gasto_uber

config = dotenv_values()
queue = asyncio.Queue()
login = config["login"]
senha = config["senha"]


async def main() -> None:
    """A função principal.
    """
    async with async_playwright() as p:
        # await logar(p, login, senha)
        links = gerar_link()
        await asyncio.gather(*[get_link(p, links, queue) for _ in range(5)])

# Eu não consigo me dar bem com o run da asyncio. Por isso sempre uso um loop de evento diferente.
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(main())
finally:
    loop.close()

breakpoint()
# Gera um arquivo csv
pd.DataFrame(result).to_csv('result.csv', sep=';',encoding='utf-8', index=False)

