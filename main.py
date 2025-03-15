from discord import (
    ApplicationContext,
    Embed,
    Message,
)
from discord.ext.bridge import Bot
from os import getenv
from view import DateSelectionView, StartView

bot = Bot()

@bot.slash_command()
async def start(ctx: ApplicationContext):
    embed = Embed(title="請選擇日期")
    view = DateSelectionView(ctx)
    await ctx.respond(embed=embed, view=view)

@bot.message_command()
async def restore(ctx: ApplicationContext, msg: Message):
    if ctx.author.bot:
        return
    if msg.author != bot.user:
        return await ctx.respond("這才不是訂票資訊...", ephemeral=True)
    if len(msg.embeds) != 1:
        return await ctx.respond("這才不是訂票資訊...", ephemeral=True)
    embed = msg.embeds[0]
    if embed.title in ["已開始搶票", "已準備好搶票，按下確認開始搶票"]:
        embed.title = "已準備好搶票，按下確認開始搶票"
    await ctx.respond(embed=embed, view=StartView(ctx))

@bot.event
async def on_ready():
    print("Bot is ready")


bot.run(getenv("TOKEN"))
