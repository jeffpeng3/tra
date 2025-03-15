from view import retryView
from io import BytesIO
from patchright.async_api import async_playwright, Page
from asyncio import sleep
from discord import (
    ApplicationContext,
    File,
)
from datetime import datetime
from classes import Ticket, Mode
from utils import generateId


async def setUID(page: Page, UID: str):
    pid = await page.query_selector("#pid")
    await pid.type(UID)


async def selectMode(page: Page, mode: Mode):
    if mode == Mode.ticket:
        s = 1
    elif mode == Mode.time:
        s = 2
    btn = await page.query_selector(
        f"#queryForm > div.basic-info > div:nth-child(3) > div.btn-group > label:nth-child({s})"
    )
    await btn.click()


async def setStartStation(page: Page, start: str):
    startSta = await page.query_selector("#startStation1")
    await startSta.type(start)


async def setEndStation(page: Page, start: str):
    startSta = await page.query_selector("#endStation1")
    await startSta.type(start)


async def setDate(page: Page, date: str):
    dateField = await page.query_selector("#rideDate1")
    await dateField.select_text()
    await dateField.type(date)


async def setStartTime(page: Page, start_time: str):
    startTime = await page.query_selector("#startTime1")
    await startTime.select_option(start_time)


async def setEndTime(page: Page, end_time: str):
    endTime = await page.query_selector("#endTime1")
    await endTime.select_option(end_time)


async def selectTrainType(page: Page, trainType: list[bool]):
    mapping = [1, 3, 4]
    for train, select in enumerate(trainType):
        if select:
            t = mapping[train]
            selector = f"#queryForm > div:nth-child(3) > div.column.byTime > div > div.trainType > label:nth-child({t})"
            btn = await page.query_selector(selector)
            await btn.click()


async def setTrain(page: Page, train: list[str]):
    for idx, t in enumerate(train):
        trainNo = await page.query_selector(f"#trainNoList{idx + 1}")
        await trainNo.type(t)


async def getResult(page: Page):
    submit = await page.query_selector("#queryForm > div.btn-sentgroup > input")
    await submit.click()
    await page.wait_for_selector("#content > div.alert.alert-info")


async def getAvailableTicket(page: Page):
    return await page.query_selector_all("input[type=radio]")


async def queryTicket(ctx: ApplicationContext, ticket: Ticket):
    UID = generateId()
    start = ticket.start
    end = ticket.end
    date = ticket.date
    start_time = ticket.start_time
    end_time = ticket.end_time

    msg = "努力翻找了一天還是沒有收穫..."
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        img = None
        for _ in range(26000):
            try:
                await page.goto(
                    "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/query"
                )
                if (
                    page.url
                    != "https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/query"
                ):
                    msg = "[網站](https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip123/query)暫時無法使用"
                    break

                await setUID(page, UID)
                await setStartStation(page, start)
                await setEndStation(page, end)
                await setDate(page, date)
                await selectMode(page, ticket.mode)

                if ticket.mode == Mode.ticket:
                    await setTrain(page, ticket.train)
                elif ticket.mode == Mode.time:
                    await setStartTime(page, start_time)
                    await setEndTime(page, end_time)
                    await selectTrainType(page, ticket.train_type)

                await getResult(page)

                all_ticket = await getAvailableTicket(page)
                if all_ticket:
                    msg = "有票拉有票拉"
                    img = await page.screenshot(type="png")
                    break
                await sleep(3)
            except Exception as e:
                print(ticket, e)
                msg = "發生錯誤"
                img = await page.screenshot(type="png")
                break
        await browser.close()
    file = None
    if img:
        file = File(BytesIO(img), "screenShot.png")
    await ctx.author.send(msg, file=file, view=retryView(ctx, ticket))
    print(datetime.now(), ticket)


# if __name__ == "__main__":
#     from classes import Ticket
#     from utils import generateId

#     ticket = Ticket(
#         UID=generateId(),
#         start="南港",
#         end="台北",
#         date="2025/4/1",
#         start_time="14:00",
#         end_time="16:00",
#     )
#     from asyncio import run

#     run(queryTicket(ApplicationContext(), ticket))
