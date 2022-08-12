import asyncio
from queue import Queue

from playwright.async_api import Playwright
from playwright._impl._api_types import TimeoutError

from uber.registro.registro import Registro

result = []


def gerar_link():
    cont = 1
    while True:
        link = 'https://riders.uber.com/v2/trips?offset=0&fromTime=&toTime=&page={}'
        _temp = link.format(cont)
        yield _temp
        cont += 1


async def logar(playwright: Playwright, login: str, password: str) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.uber.com/br/pt-br/")
    await page.locator("text=Fazer login").click()
    await page.locator("text=Faça login para viajar").click()
    async with page.expect_popup() as popup_info:
        await page.locator("[data-test=\"facebook\"]").click()
    page1 = await popup_info.value
    await page1.locator("[placeholder=\"Email ou telefone\"]").fill(login)
    await page1.locator("[placeholder=\"Senha\"]").fill(password)
    async with page1.expect_navigation():
        await page1.locator("button:has-text(\"Entrar\")").click()
    await page1.close()
    await page.locator("text=Onde você quer que o motorista te busque?").wait_for()
    await page.close()
    await context.storage_state(path="state.json")


async def get_link(playwright: Playwright, links, queue: Queue) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="state.json")
    page = await context.new_page()
    await page.goto('https://riders.uber.com/trips')
    for link in links:
        await page.goto(link)
        cards = page.locator("section")
        count = await cards.count()
        contador = 0
        while count == 0:
            try:
                await page.locator("text=Nenhuma viagem encontrada no período selecionado").wait_for(timeout=1000)
                await context.close()
                await browser.close()
                return
            except TimeoutError:
                pass
            await asyncio.sleep(0.5)
            cards = page.locator("section")
            count = await cards.count()
            contador += 1
            if contador == 10:
                breakpoint()
        for i in range(count):
            try:
                await cards.nth(i).locator('span:has-text("Cancelada") >> nth=0').wait_for(timeout=1000)
                continue
            except TimeoutError:
                pass
            try:
                await cards.nth(i).click()
            except:
                await page.pause()
            try:
                await page.locator("text=Sua viagem").wait_for(timeout=3000)
                await get_dados(page)
            except TimeoutError:
                continue
            finally:
                await page.locator("text=Arrow leftVoltar para as viagens").click()


async def get_dados(page) -> None:
    elementos = {"categoria": "Car front", "quilometro": "Road",
                 "tempo": "Clock", "valor": "Tag", "pagamento": "Credit card"}
    temp_dict = {}
    try:
        local_data = await page.locator("._css-dZTBoz").inner_text(timeout=3000)
    except TimeoutError:
        await page.reload()
        try:
            local_data = await page.locator("._css-dZTBoz").inner_text(timeout=3000)
        except TimeoutError:
            return

    for k, v in elementos.items():
        try:
            valor = await page.locator(f'p:right-of(:has-text("{v}"))').first.inner_text(timeout=1000)
            temp_dict[k] = valor
        except TimeoutError:
            temp_dict[k] = None
    rota = await page.locator("._css-bFaaKw").inner_text(timeout=3000)
    try:
        dados = await Registro.to_registro(datas=local_data, rotas=rota, **temp_dict)
    except IndexError:
        breakpoint()
    except AttributeError:
        breakpoint()
    print(dados)
    result.append(dados)
