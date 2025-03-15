from io import BytesIO
from patchright.async_api import async_playwright
from asyncio import sleep, create_task
from discord.commands import option
from discord import (
    Bot,
    AutocompleteContext,
    ApplicationContext,
    ButtonStyle,
    Interaction,
    Message,
    File,
)
from utils import station, time
from datetime import date, timedelta, datetime
from discord.ui import View, button, Button
from dataclasses import dataclass
from os import getenv

bot = Bot()


async def stationComplete(ctx: AutocompleteContext):
    ret = [*filter(lambda x: ctx.value in x, station)] if ctx.value else station
    return ret[:25]


async def timeComplete(ctx: AutocompleteContext):
    ret = [*filter(lambda x: ctx.value in x, time)] if ctx.value else time
    return ret[:25]


async def dateComplete(ctx: AutocompleteContext):
    d = date.today()
    lst = []
    for i in range(30):
        lst.append((d := d + timedelta(1)).strftime("%Y%m%d"))
    ret = [*filter(lambda x: ctx.value in x, lst)] if ctx.value else lst
    return ret[:25]


@dataclass
class Ticket:
    UID: str
    start: str
    end: str
    date: str
    start_time: str
    end_time: str


@bot.slash_command()
@option(
    name="id",
    description="身分證字號(我也不知道為什麼要有)",
    type=str,
    min_length=10,
    max_length=10,
)
@option(name="start", description="起始站", type=str, autocomplete=stationComplete)
@option(name="end", description="終點站", type=str, autocomplete=stationComplete)
@option(name="date", type=str, autocomplete=dateComplete)
@option(name="start_time", type=str, autocomplete=timeComplete)
@option(name="end_time", type=str, autocomplete=timeComplete)
async def start(
    ctx: ApplicationContext,
    id: str,
    start: str,
    end: str,
    date: str,
    start_time: str,
    end_time: str,
):
    print(id, start, end, date, start_time, end_time)
    if start == end:
        await ctx.respond("起始站與終點站不可相同")
        return
    if start_time > end_time:
        await ctx.respond("起始時間不可大於結束時間")
        return
    ticket = Ticket(id, start, end, date, start_time, end_time)
    create_task(query_ticket(ctx, ticket))
    await ctx.respond(f"{date}\n從: {start} 到 {end}\n{start_time}~{end_time}")


class retryView(View):
    def __init__(
        self,
        ctx: ApplicationContext,
        ticket: Ticket,
    ) -> None:
        super().__init__(timeout=60)
        self.ctx = ctx
        self.ticket = ticket

    @button(style=ButtonStyle.gray, emoji="🔄", label="再來一張")
    async def retry(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        self.disable_all_items()
        self.stop()
        await interaction.message.delete()
        await self.ctx.author.send(content="已重新開始撈票", delete_after=10)
        create_task(query_ticket(self.ctx, self.ticket))


async def query_ticket(ctx: ApplicationContext, ticket: Ticket):
    UID = ticket.UID
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

                pid = await page.query_selector("#pid")
                await pid.type(UID)

                btn = await page.query_selector(
                    "#queryForm > div.basic-info > div:nth-child(3) > div.btn-group > label:nth-child(2)"
                )
                await btn.click()

                startSta = await page.query_selector("#startStation1")
                await startSta.type(start)

                dest = await page.query_selector("#endStation1")
                await dest.type(end)

                dateField = await page.query_selector("#rideDate1")
                await dateField.select_text()
                await dateField.type(date)

                startTime = await page.query_selector("#startTime1")
                await startTime.select_option(start_time)

                endtime = await page.query_selector("#endTime1")
                await endtime.select_option(end_time)

                btn3000 = await page.query_selector(
                    "#queryForm > div:nth-child(3) > div.column.byTime > div > div.trainType > label:nth-child(1)"
                )
                await btn3000.click()

                btnPuyuma = await page.query_selector(
                    "#queryForm > div:nth-child(3) > div.column.byTime > div > div.trainType > label:nth-child(3)"
                )
                await btnPuyuma.click()

                btnzhuchun = await page.query_selector(
                    "#queryForm > div:nth-child(3) > div.column.byTime > div > div.trainType > label:nth-child(4)"
                )
                await btnzhuchun.click()
                submit = await page.query_selector("#queryForm > div.btn-sentgroup > input")
                await submit.click()
                await page.wait_for_selector("#content > div.alert.alert-info")

                all_ticket = await page.query_selector_all("input[type=radio]")
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


bot.run(getenv("TOKEN"))
