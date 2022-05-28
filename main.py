import asyncio

import pandas as pd
from playwright.async_api import async_playwright
from uber.pages.pages import gerar_link, run, pagamento, gerar_url, result, logar

async def main() -> None:
    async with async_playwright() as p:
        await logar(p)
        links = gerar_link()
        await asyncio.gather(*[run(p, links) for _ in range(5)])
        url_link = gerar_url(result)
        await asyncio.gather(*[pagamento(p, url_link) for _ in range(5)])

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

loop.close()
pd.DataFrame(result).to_csv('result.csv', sep=';', encoding='1252', index=False)