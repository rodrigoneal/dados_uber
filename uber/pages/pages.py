import asyncio

from playwright.async_api import Playwright
from playwright._impl._api_types import TimeoutError as PlayTimeoutError


from uber.registro.registro import Registro
result = []

def gerar_link():
    cont = 0
    while True:
        link = 'https://riders.uber.com/trips?offset={}&fromTime&toTime'
        _temp = link.format(cont)
        yield _temp
        cont += 10


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




async def run(playwright: Playwright, links) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(storage_state="state.json")
    page = await context.new_page()
    await page.goto('https://riders.uber.com/trips')
    for link in links:
        print(link)
        await page.goto(link)
        if await page.locator("text=Parece que você ainda não fez nenhuma viagem.").is_visible():
            await context.close()
            await browser.close()
            return

        while True:
            # Essa desgraça de site é um cu pra automatizar. Por isso tenho que clicar no card e esperar que ele esteja aberto.
            try:
                await page.locator('svg:has-text("Plus")').first.click(timeout=1000, force=True)
                await asyncio.sleep(1)
            except:
                cards_fechado = page.locator('svg:has-text("Minus")')
                count = await cards_fechado.count()
                if count > 1:
                    break
                else:
                    await page.reload()
                    await asyncio.sleep(2)


        cards_fechado = page.locator('svg:has-text("Minus")')
        count = await cards_fechado.count()
        _local = page.locator('.d6')
        for i in range(count):
            _links = page.locator('a:has-text("Informações")')
            _count = await _links.count()
            _link = await _links.nth(_count - 1).get_attribute('href')
            local = await _local.nth(i).inner_text()
            reg = await Registro.to_registro(local)

            reg.link = _link
            result.append(reg)
    await context.close()
    await browser.close()


    

