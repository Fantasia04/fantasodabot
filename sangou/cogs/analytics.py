import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import shutil
import os
from helpers.datafiles import get_file, set_file


class Analytics(Cog):
    """
    I need to know. I NEED to know!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def stats(self, ctx):
        """This shows your analytics.

        It only shows the most recent command uses,
        since I'm currently too lazy to code a page system.

        No arguments."""
        useranalytics = get_file("analytics", f"users/{ctx.author.id}")
        if not useranalytics:
            return await ctx.reply(
                content="There are no analytics to show.", mention_author=False
            )
        contents = ""
        for key, value in list(useranalytics.items())[-10:]:
            contents += f"\n`{key}` | Used **{value['success']}** times, failed **{value['failure']}** times."
        contents += f"\n\nYou have used **{len(useranalytics.keys())}**/{len(self.bot.commands)} commands.\nYour completion score is **{round(len(useranalytics.keys())/len(self.bot.commands)*100, 2)}**%."
        await ctx.reply(content=contents, mention_author=False)

    @commands.bot_has_permissions(attach_files=True)
    @commands.command()
    async def mydata(self, ctx):
        """This gives you your data.

        It zips up the entirety of your users folder.
        It does not include reminders, as that is on a separate system.

        No arguments."""
        try:
            shutil.make_archive(
                f"data/{ctx.author.id}", "zip", f"data/users/{ctx.author.id}"
            )
            sdata = discord.File(f"data/{ctx.author.id}.zip")
            await ctx.message.reply(
                content=f"`{ctx.author}`'s data...",
                file=sdata,
                mention_author=False,
            )
            os.remove(f"data/{ctx.author.id}.zip")
        except FileNotFoundError:
            await ctx.message.reply(
                content="You don't have any data.",
                mention_author=False,
            )

    @stats.command()
    async def enable(self, ctx):
        """This enables analytics collection.

        Please see the [privacy notice](https://3gou.0ccu.lt/introduction/privacy-notice/).

        No arguments."""
        userdata = get_file("botusers")
        if "nostats" not in userdata:
            userdata["nostats"] = []
        if ctx.author.id not in userdata["nostats"]:
            return await ctx.reply(
                content="You already have analytics toggled on.", mention_author=False
            )
        userdata["nostats"].remove(ctx.author.id)
        set_file("botusers", json.dumps(userdata))
        return await ctx.reply(
            content="**Analytics for you have been toggled on.**",
            mention_author=False,
        )

    @stats.command()
    async def disable(self, ctx):
        """This disables analytics collection.

        Please see the [privacy notice](https://3gou.0ccu.lt/introduction/privacy-notice/).
        It will delete your analytics data as well.

        No arguments."""
        userdata = get_file("botusers")
        if "nostats" not in userdata:
            userdata["nostats"] = []
        if ctx.author.id in userdata["nostats"]:
            return await ctx.reply(
                content="You already have analytics toggled off.", mention_author=False
            )
        userdata["nostats"].append(ctx.author.id)
        set_file("botusers", json.dumps(userdata))
        useranalytics = get_file("analytics", f"users/{ctx.author.id}")
        if not useranalytics:
            return await ctx.reply(
                content="**Analytics for you have been toggled off.**\nAnalytics were not deleted as there is nothing to delete.",
                mention_author=False,
            )
        set_file("analytics", json.dumps({}), f"users/{ctx.author.id}")
        await ctx.reply(
            content="**Analytics for you have been toggled off.**",
            mention_author=False,
        )

    @Cog.listener()
    async def on_command_error(self, ctx, error):
        await self.bot.wait_until_ready()
        userdata = get_file("botusers")
        if (
            ctx.author.bot
            or "nostats" in userdata
            and ctx.author.id in userdata["nostats"]
        ):
            return
        useranalytics = get_file("analytics", f"users/{ctx.author.id}")

        if not useranalytics:
            try:
                await ctx.author.send(
                    content=f"📡 **Analytics Warning**\nThis is a one-time notice to inform you that commands used are logged for analytics purposes.\nPlease see the below link for more information.\n> <https://3gou.0ccu.lt/introduction/privacy-notice/>\n\nIf you do not consent to this, please run `{ctx.prefix}stats disable`.\nThis will disable user analytics collection for you, and delete your analytics data."
                )
            except:
                # don't save analytics unless user is informed
                return

        if str(ctx.command) not in useranalytics:
            useranalytics[str(ctx.command)] = {
                "success": 0,
                "failure": 0,
            }

        useranalytics[str(ctx.command)]["failure"] += 1
        set_file("analytics", json.dumps(useranalytics), f"users/{ctx.author.id}")

    @Cog.listener()
    async def on_command_completion(self, ctx):
        await self.bot.wait_until_ready()
        userdata = get_file("botusers")
        if (
            ctx.author.bot
            or "nostats" in userdata
            and ctx.author.id in userdata["nostats"]
        ):
            return
        useranalytics = get_file("analytics", f"users/{ctx.author.id}")

        if not useranalytics:
            try:
                await ctx.author.send(
                    content=f"📡 **Analytics Warning**\nThis is a one-time notice to inform you that commands used are logged for analytics purposes.\nPlease see the below link for more information.\n> <https://3gou.0ccu.lt/introduction/privacy-notice/>\n\nIf you do not consent to this, please run `{ctx.prefix}stats disable`.\nThis will disable user analytics collection for you, and delete your analytics data."
                )
            except:
                # don't save analytics unless user is informed
                return

        if str(ctx.command) not in useranalytics:
            useranalytics[str(ctx.command)] = {
                "success": 0,
                "failure": 0,
            }

        useranalytics[str(ctx.command)]["success"] += 1
        set_file("analytics", json.dumps(useranalytics), f"users/{ctx.author.id}")


async def setup(bot):
    await bot.add_cog(Analytics(bot))
