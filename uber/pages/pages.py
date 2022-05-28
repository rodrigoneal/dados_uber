import asyncio
from typing import List
import urllib.parse

from playwright.async_api import Playwright
from playwright._impl._api_types import TimeoutError as PlayTimeoutError


from uber.registro.registro import Registro

def gerar_link():
    cont = 0
    while True:
        link = 'https://riders.uber.com/trips?offset={}&fromTime&toTime'
        _temp = link.format(cont)
        yield _temp
        cont += 10

def gerar_url(dados: List[Registro]):
    root = 'https://riders.uber.com/'
    for dado in dados:
        if not dado.metodo_pagamento:
            yield (urllib.parse.urljoin(root, dado.link), dado)


async def logar(playwright: Playwright, login, senha) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()    
    page = await context.new_page()
    await page.goto("https://www.uber.com/br/pt-br/")
    await page.locator("text=Fazer login").click()
    await page.locator("text=Faça login para viajar").click()
    await page.locator("text=Ou entre usando uma conta de rede social").click()
    async with page.expect_navigation():
        await page.locator("text=Facebook").click()
    await page.locator("[placeholder=\"Email ou telefone\"]").fill(login)
    await page.locator("[placeholder=\"Senha\"]").fill(senha)
    async with page.expect_navigation():
        await page.locator("[placeholder=\"Senha\"]").press("Enter")
    await context.storage_state(path="state.json")

result = []

async def run(playwright: Playwright, links) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="state.json")
    page = await context.new_page()
    await page.goto('https://riders.uber.com/trips')
 

    for link in links:
        await page.goto(link)
        cards = page.locator(".d8 svg")
        locals = page.locator('.d6')
        

        count = await cards.count()
        if count < 1:
            await context.close()
            await browser.close()
            return
        for i in range(count):
            try:
                await cards.nth(i).click()
            except PlayTimeoutError:
                await page.reload()   
                await cards.nth(i).click()     
            espera = 0
            while True:
                try:
                    local = await locals.nth(i).text_content()
                except:
                    continue
                await asyncio.sleep(0.1)
                if local.startswith('Minus'):
                    break
                if espera % 5 == 0:
                    try:
                        await cards.nth(i).click()
                        await asyncio.sleep(0.1)
                    except PlayTimeoutError:
                        page.reload()
                        await cards.nth(i).click()
                espera += 1
            _links = page.locator('a:has-text("Informações")')
            _count = await _links.count()
            _link = await _links.nth(_count - 1).get_attribute('href')
            local = await locals.nth(i).inner_text()
            reg = await Registro.to_registro(local)
            reg.link = _link
            result.append(reg)

async def pagamento(playwright: Playwright, links) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="state.json")
    page = await context.new_page()
    for link, dado in links:
        try:
            await page.goto(link)
        except: await page.goto(link)
        try:
            await page.locator("text=Ver recibo").click(timeout=5000)
        except PlayTimeoutError:
            try:
                await page.locator("text=Estamos gerando o recibo da viagem. Tente de novo mais tarde.").wait_for(timeout=2000)
                return
            except PlayTimeoutError:
                continue
        try:
            texto = await page.frame_locator("#unified-receipt-iframe").locator(":nth-match(:text('••••'), 1), :nth-match(:text('Dinheiro'), 1)").text_content(timeout=5000)
        except PlayTimeoutError:
            try:
                await page.locator("text=Ver recibo").click(timeout=5000)
            except PlayTimeoutError:
                continue
            try:
                texto = await page.frame_locator("#unified-receipt-iframe").locator(":nth-match(:text('••••'), 1), :nth-match(:text('Dinheiro'), 1)").text_content(timeout=5000)
            except PlayTimeoutError:
                dado.metodo_pagamento = None
                continue
        dado.metodo_pagamento = texto.strip()

        print(texto)

    await context.close()
    await browser.close()


    

