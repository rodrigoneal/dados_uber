import asyncio


from playwright.async_api import Playwright, Locator
from playwright._impl._api_types import TimeoutError

from uber.registro.registro import Registro

result = []


async def get_erro(page, link):
    for _ in range(10):
        try:
            await page.locator("text=nav.mytrips").first.hover(timeout=500)
            await asyncio.sleep(1.5)
            await page.goto(link)
        except TimeoutError:
            try:
                await page.locator("text=too many requests").first.hover(timeout=500)
                await asyncio.sleep(1.5)
                await page.goto(link)
            except TimeoutError:
                try:
                    await page.locator("text=Falha ao carregar, tente de novo mais tarde.").first.hover(timeout=500)
                    await asyncio.sleep(1.5)
                    await page.goto(link)
                except TimeoutError:
                    try:
                        await page.locator("text=generic.error").first.hover(timeout=500)
                        await asyncio.sleep(1.5)
                        await page.goto(link)
                    except TimeoutError:
                        return


def gerar_link():
    cont = 1
    while True:
        link = 'https://riders.uber.com/trips?page={}'
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
    await page1.locator("button:has-text(\"Entrar\")").click()
    await page.locator("text=Onde você quer que o motorista te busque?").wait_for()
    await context.storage_state(path="state.json")
    await page1.close()
    await page.close()


async def open_cards(card: Locator, page: Playwright, index: int, link):
    try:
        await card.nth(index).locator('span:has-text("Cancelada") >> nth=0').wait_for(timeout=1000)
        return False
    except TimeoutError:
        pass
    for _ in range(10):
        try:
            if index == 0:
                await card.first.click()
            else:
                await card.nth(index).click()
        except TimeoutError:
            await page.goto(link)
        await asyncio.sleep(0.5)
        if page.url != link:
            link = page.url
            break
    for i in range(10):
        await get_erro(page, link)
        try:
            await page.locator("._css-ggwCcI").first.wait_for(timeout=1000)
            await page.get_by_role("radio", name="rating").first.wait_for(timeout=500)
            return True
        except TimeoutError:
            try:
                await page.locator("._css-krCBTw").first.wait_for(timeout=500, state="visible")
                return False
            except TimeoutError:
                await page.goto(link)
                await get_erro(page, link)
        if i == 9:
            return False

num_paginas = None


async def get_link(playwright: Playwright, links, queue) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="state.json")
    page = await context.new_page()
    await page.goto('https://riders.uber.com/trips')
    global num_paginas
    while num_paginas is None:
        try:
            num_paginas = await page.locator("._css-bucRsj").inner_text(timeout=500)
            num_paginas = int(num_paginas.split(" ")[-1])
        except TimeoutError:
            pass
    print(num_paginas)
    for link in links:
        paginate = int(link.split("=")[-1])
        print(paginate)
        pronto = round(paginate / num_paginas * 100, 2)
        print(f"{pronto}% concluido.")
        if paginate > num_paginas:
            await context.close()
            await browser.close()
            return
        await page.goto(link)
        await get_erro(page, link)

        for i in range(10):
            cards = page.locator("section")
            try:
                await cards.first.wait_for(timeout=500)
                break
            except:
                await page.goto(link)

        count = await cards.count()
        for i in range(count):
            resposta = await open_cards(cards, page, i, link)
            if resposta:
                await get_dados(page, link)
            else:
                await page.goto(link)
            await asyncio.sleep(0.5)


async def get_dados(page: Playwright, link) -> None:
    elementos = {"categoria": "Car front", "quilometro": "Road",
                 "tempo": "Clock", "valor": "Tag", "pagamento": "Credit card"}
    temp_dict = {}

    for i in range(10):
        await get_erro(page, link)
        try:
            local_data = await page.locator("._css-dZTBoz").inner_text(timeout=1000)
            rota = await page.locator("._css-bFaaKw").inner_text(timeout=500)
            break
        except TimeoutError:
            await page.goto(link)
        if i == 10:
            await page.goto(link)
            return

    for k, v in elementos.items():
        try:
            valor = await page.locator(f'p:right-of(:has-text("{v}"))').first.inner_text(timeout=1000)
            temp_dict[k] = valor
        except TimeoutError:
            temp_dict[k] = None
    try:
        dados = await Registro.to_registro(datas=local_data, rotas=rota, **temp_dict)
    except IndexError:
        return
    except ValueError:
        return
    except UnboundLocalError:
        return
    finally:
        for _ in range(10):
            if page.url != link:
                await page.goto(link)
                await asyncio.sleep(1)
            else:
                pass
    result.append(dados)
