# from tra_spider import query_ticket
from discord import (
    ApplicationContext,
    ButtonStyle,
    Interaction,
    Message,
)
from discord.ui import View, button, Button, Select, Modal, InputText
from classes import Ticket
from datetime import date, timedelta
from utils import station

GREEN = ButtonStyle.green
RED = ButtonStyle.red
GRAY = ButtonStyle.gray
BLURPLE = ButtonStyle.blurple

class retryView(View):
    def __init__(
        self,
        ctx: ApplicationContext,
        ticket: Ticket,
    ) -> None:
        super().__init__(timeout=60)
        self.ctx = ctx
        self.ticket = ticket

    @button(style=ButtonStyle.gray, label="再來一張")
    async def retry(self, btn: Button, interaction: Interaction):
        await interaction.response.defer()
        if not isinstance(interaction.message, Message):
            return
        self.disable_all_items()
        self.stop()
        self.ticket.submit(self.ctx)
        await interaction.message.delete()
        await self.ctx.author.send(content="已重新開始撈票", delete_after=10)


class StartView(View):
    def __init__(self, ctx: ApplicationContext):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.add_item(Button(label="開始", style=GREEN, custom_id="start"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.custom_id == "start":
            await interaction.response.defer()
            embed = interaction.message.embeds[0]
            ticket = Ticket.from_embed(embed)
            ticket.submit(self.ctx)
            print(ticket)
            # create_task(query_ticket(self.ctx, ticket))
            embed.title = "已開始搶票"
            await interaction.message.edit(embed=embed, view=None)
        return True


class ModelSelectionView(View):
    def __init__(self, ctx: ApplicationContext):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.add_item(Button(label="新自強", style=GREEN, custom_id="newtc"))
        self.add_item(Button(label="普悠瑪", style=GREEN, custom_id="pym"))
        self.add_item(Button(label="自強號", style=GRAY, custom_id="tc"))
        self.add_item(Button(label="確定", style=RED, custom_id="confirm"))

    def matchCustomId(self, custom_id: str) -> Button:
        return [*filter(lambda x: x.custom_id == custom_id, self.children)][0]

    def allowModel(self) -> bool:
        return map(lambda x: x.label, filter(lambda x: x.style == GREEN, self.children))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.custom_id in ["newtc", "pym", "tc"]:
            if not (btn := self.matchCustomId(interaction.custom_id)):
                interaction.response.send_message(
                    "發生錯誤，請稍後再嘗試", ephemeral=True
                )
                return True
            btn.style = GRAY if btn.style == GREEN else GREEN
            await self.message.edit(view=self)
            await interaction.response.defer()
        elif interaction.custom_id == "confirm":
            s = " ".join(self.allowModel())
            embed = interaction.message.embeds[0]
            embed.title = "已準備好搶票，按下確認開始搶票"
            embed.add_field(name="車種", value=s, inline=False)
            view = StartView(self.ctx)
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.defer()
        return True


class HourSelectionView(View):
    def __init__(self, ctx: ApplicationContext, time_type: str, period: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.time_type = time_type
        self.period = period
        self.add_hour_buttons()

    def add_hour_buttons(self):
        for idx, val in enumerate([12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]):
            self.add_item(
                Button(
                    label=str(val),
                    custom_id=f"{(12 if self.period == 'PM' else 0) + (0 if val == 12 else val):02d}:00",
                    row=idx // 4,
                )
            )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.custom_id:
            selected_time = interaction.custom_id
            view = None
            embed = interaction.message.embeds[0]
            embed.add_field(
                name=f"{self.time_type}時間", value=selected_time, inline=False
            )
            if self.time_type == "開始":
                embed.title = "請選擇結束時間"
                view = TimeSelectionView(self.ctx, "結束")
            else:
                embed.title = "請選擇起點站"
                view = ModelSelectionView(self.ctx)
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.defer()
            self.stop()
        return True


class TimeSelectionView(View):
    def __init__(self, ctx: ApplicationContext, time_type: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.time_type = time_type
        self.add_item(Button(label="AM", custom_id="AM"))
        self.add_item(Button(label="PM", custom_id="PM"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.custom_id in ["AM", "PM"]:
            await interaction.message.edit(
                view=HourSelectionView(self.ctx, self.time_type, interaction.custom_id)
            )
            await interaction.response.defer()
            self.stop()
        return True


class SerialSelectModal(Modal):
    def __init__(self, ctx: ApplicationContext):
        super().__init__(title="請輸入車次，車次一必填，其餘選填")
        self.ctx = ctx
        self.add_item(InputText(label="車次一", required=True, custom_id="train1"))
        self.add_item(InputText(label="車次二", required=False, custom_id="train2"))
        self.add_item(InputText(label="車次三", required=False, custom_id="train3"))

    async def callback(self, interaction: Interaction):
        try:
            trainList = " ".join(
                item["components"][0]["value"]
                for item in interaction.data["components"]
                if item["components"][0]["value"].isdigit()
            )
        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "發生錯誤，請稍後再嘗試", ephemeral=True
            )
            return
        if not trainList:
            await interaction.response.send_message("請輸入車次", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.title = "已準備好搶票，按下確認開始搶票"
        embed.add_field(name="車次", value=trainList, inline=False)
        view = StartView(self.ctx)
        await interaction.message.edit(embed=embed, view=view)
        await interaction.response.defer()


class SerialSelectionView(View):
    def __init__(self, ctx: ApplicationContext):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.add_item(Button(label="設定車次", style=BLURPLE, custom_id="confirm"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        await interaction.response.send_modal(SerialSelectModal(self.ctx))


class ModeSelectView(View):
    def __init__(self, ctx: ApplicationContext) -> None:
        super().__init__(timeout=60)
        self.ctx = ctx
        self.add_item(Button(label="以車次訂票", style=GREEN, custom_id="ticket"))
        self.add_item(Button(label="以時間訂票", style=GREEN, custom_id="time"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        embed = interaction.message.embeds[0]
        view = None
        if interaction.custom_id == "ticket":
            embed.title = "請輸入車次"
            embed.add_field(name="模式", value="車次", inline=False)
            view = SerialSelectionView(self.ctx)
        elif interaction.custom_id == "time":
            embed.title = "請選擇開始時間"
            embed.add_field(name="模式", value="時間", inline=False)
            view = TimeSelectionView(self.ctx, "開始")
        await interaction.response.defer()
        await interaction.message.edit(embed=embed, view=view)
        return True


class StationSelectionView(View):
    def __init__(self, ctx: ApplicationContext, mode: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.mode = mode
        self.add_station_buttons()

    def add_station_buttons(self):
        for s in station:
            self.add_item(
                Button(
                    label=s.split("-")[1],
                    style=BLURPLE,
                    custom_id=s,
                )
            )

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.custom_id:
            selected_station = interaction.custom_id
            view = None
            embed = interaction.message.embeds[0]
            embed.add_field(
                name=f"{self.mode}站",
                value=selected_station,
                inline=False,
            )
            if self.mode == "起點":
                embed.title = "請選擇終點站"
                view = StationSelectionView(self.ctx, "終點")
            else:
                embed.title = "請選擇模式"
                view = ModeSelectView(self.ctx)
            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.defer()
            self.stop()
        return True


class DateSelectionView(View):
    def __init__(self, ctx: ApplicationContext, page: int = 1):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.page = page
        self.add_date_dropdown()
        self.add_navigation_buttons()

    def add_date_dropdown(self):
        options = []
        today = date.today()
        start_day = (self.page - 1) * 15
        select = Select(placeholder="選擇日期", options=options)
        for i in range(start_day, start_day + 15):
            date_str = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            select.add_option(label=date_str, value=date_str)
        self.add_item(select)

    def add_navigation_buttons(self):
        if self.page > 1:
            self.add_item(Button(label="上一頁", custom_id="prev"))
        if self.page < 2:
            self.add_item(Button(label="下一頁", custom_id="next"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        await interaction.response.defer()
        if interaction.data.get("values"):
            selected_date = interaction.data["values"][0]
            embed = interaction.message.embeds[0]
            embed.title = "請選擇起點站"
            embed.add_field(name="日期", value=selected_date, inline=False)
            view = StationSelectionView(self.ctx, "起點")
            await interaction.message.edit(embed=embed, view=view)
        elif interaction.custom_id == "prev":
            await interaction.message.edit(view=DateSelectionView(self.ctx, 1))
        elif interaction.custom_id == "next":
            await interaction.message.edit(view=DateSelectionView(self.ctx, 2))
        return True
