import config
import datetime
import discord
import json
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.datafiles import get_guildfile
from helpers.embeds import stock_embed
from helpers.datafiles import get_guildfile, set_guildfile


class TSAR(Cog):
    """
    True. Self. Assignable. Roles.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    async def role(self, ctx, *, role):
        tsars = get_guildfile(ctx.guild.id, "tsar")
        if not tsars:
            return await ctx.reply(
                content="You cannot get a role when no roles are configured.",
                mention_author=False,
            )
        try:
            for name, tsar in list(tsars.items()):
                if name.lower() == role.lower():
                    roledata = tsar
                    rolename = name
            if rolename:
                pass
        except:
            return await ctx.reply(
                content=f"There is no role named `{role}`.", mention_author=False
            )

        if roledata["blacklisted"]:
            badroles = [
                badrole
                for badrole in [
                    ctx.guild.get_role(int(r)) for r in roledata["blacklisted"]
                ]
            ]
            if any([n in ctx.author.roles for n in badroles]):
                return await ctx.reply(
                    content=f"You cannot get this role, as you have {', '.join(['`' + r.name + '`' for r in badroles if r in ctx.author.roles])}.",
                    mention_author=False,
                )

        if roledata["required"]:
            mustroles = [
                mustrole
                for mustrole in [
                    ctx.guild.get_role(int(r)) for r in roledata["required"]
                ]
            ]
            if any([n not in ctx.author.roles for n in mustroles]):
                return await ctx.reply(
                    content=f"You cannot get this role, as you don't have {', '.join(['`' + r.name + '`' for r in mustroles if r not in ctx.author.roles])}.",
                    mention_author=False,
                )

        if roledata["mindays"]:
            usertracks = get_guildfile(ctx.guild.id, "usertrack")
            if str(ctx.author.id) not in usertracks and roledata["mindays"] != 0:
                return await ctx.reply(
                    content=f"You cannot get this role, as you must wait `{roledata['mindays'] - 0}` days.",
                    mention_author=False,
                )
            elif roledata["mindays"] > usertracks[str(ctx.author.id)]["truedays"]:
                return await ctx.reply(
                    content=f"You cannot get this role, as you must wait `{roledata['mindays'] - usertracks[str(ctx.author.id)]['truedays']}` days.",
                    mention_author=False,
                )

        actualrole = ctx.guild.get_role(roledata["roleid"])
        if actualrole in ctx.author.roles:
            await ctx.author.remove_roles(actualrole)
            return await ctx.reply(
                content=f"`{actualrole}` was removed from your roles.",
                mention_author=False,
            )
        else:
            await ctx.author.add_roles(actualrole)
            return await ctx.reply(
                content=f"`{actualrole}` was added to your roles.", mention_author=False
            )

    @commands.guild_only()
    @commands.command()
    async def roles(self, ctx):
        tsars = get_guildfile(ctx.guild.id, "tsar")
        embed = stock_embed(self.bot)
        embed.title = "🎫 Assignable Roles"
        embed.description = (
            f"Use `{ctx.prefix}role` with the name to get or remove a role."
        )
        embed.color = discord.Color.gold()
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if not tsars:
            embed.add_field(
                name="None",
                value="There are no assignable roles.",
                inline=False,
            )
        else:
            for name, tsar in list(tsars.items()):
                fieldval = (
                    f"> **Role:** {ctx.guild.get_role(tsar['roleid']).mention}\n"
                    + f"> **Minimum Days:** `{tsar['mindays']}`\n"
                    + f"> **Forbidden Roles:** "
                )
                fieldval += (
                    ", ".join(
                        [
                            ctx.guild.get_role(int(s)).mention
                            for s in tsar["blacklisted"]
                        ]
                    )
                    if tsar["blacklisted"]
                    else "None"
                )
                fieldval += "\n" + f"> **Required Roles: **"
                fieldval += (
                    ", ".join(
                        [ctx.guild.get_role(int(s)).mention for s in tsar["required"]]
                    )
                    if tsar["required"]
                    else "None" + "\n"
                )
                embed.add_field(
                    name=name,
                    value=fieldval,
                    inline=False,
                )

        return await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def tsar(self, ctx):
        tsars = get_guildfile(ctx.guild.id, "tsar")

        navigation_reactions = ["⏹", "✨", "❌", "💣"]

        embed = stock_embed(self.bot)
        embed.title = "⚙️ TSAR Configuration Editor"
        embed.color = ctx.author.color
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if not tsars:
            embed.add_field(
                name="Currently empty!",
                value="Click the sparkle icon to get started.",
                inline=False,
            )
        else:
            for name, tsar in list(tsars.items()):
                fieldval = (
                    f"> **Role:** {ctx.guild.get_role(tsar['roleid']).mention}\n"
                    + f"> **Minimum Days:** `{tsar['mindays']}`\n"
                    + f"> **Forbidden Roles:** "
                )
                fieldval += (
                    ", ".join(
                        [
                            ctx.guild.get_role(int(s)).mention
                            for s in tsar["blacklisted"]
                        ]
                    )
                    if tsar["blacklisted"]
                    else "None"
                )
                fieldval += "\n" + f"> **Required Roles: **"
                fieldval += (
                    ", ".join(
                        [ctx.guild.get_role(int(s)).mention for s in tsar["required"]]
                    )
                    if tsar["required"]
                    else "None" + "\n"
                )
                embed.add_field(
                    name=name,
                    value=fieldval,
                    inline=False,
                )
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for e in navigation_reactions:
            await configmsg.add_reaction(e)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in navigation_reactions

        def messagecheck(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            return await configmsg.edit(
                content="Operation timed out.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

        async def waitformsg():
            try:
                message = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                await configsuppmsg.delete()
                return await configmsg.edit(
                    content="Operation timed out.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )
            return message

        if str(reaction) == "⏹":
            return await configmsg.edit(
                content="Operation cancelled.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "✨":
            if len(tsars) == 20:
                return await ctx.reply(
                    content="Unable to create new TSAR: Maximum of 20 reached.",
                    mention_author=False,
                )
            namemsg = await ctx.send(content="**Making new TSAR.**\nName of this TSAR?")
            nameresp = await waitformsg()
            if nameresp.content.lower() in dict(
                (k.lower(), v) for k, v in tsars.items()
            ):
                await configmsg.delete()
                return await namemsg.edit(
                    content=f"Unable to proceed: TSAR already exists.", delete_after=5
                )
            await namemsg.edit(
                content=f"TSAR Name: `{nameresp.content}`", delete_after=5
            )
            IDmsg = await ctx.send(content="ID of the role to give?")
            IDresp = await waitformsg()
            await IDmsg.edit(content=f"Role ID: `{IDresp.content}`", delete_after=5)
            mindaysmsg = await ctx.send(content="Minimum days?")
            mindaysresp = await waitformsg()
            await mindaysmsg.edit(
                content=f"Minimum days: `{mindaysresp.content}`", delete_after=5
            )
            blacklistedrolesmsg = await ctx.send(
                content="Roles forbidden? (IDs separated by spaces, or none for none)"
            )
            blacklistedrolesresp = await waitformsg()
            content = f"Forbidden roles: `{blacklistedrolesresp.content}`"
            if any([o == IDresp.content for o in blacklistedrolesresp.content.split()]):
                content += (
                    "\nYou specified the same Role ID, so this TSAR will be give only."
                )
            await blacklistedrolesmsg.edit(
                content=content,
                delete_after=5,
            )
            requiredrolesmsg = await ctx.send(
                content="Roles required? (IDs separated by spaces, or none for none)"
            )
            requiredrolesresp = await waitformsg()
            if any(
                [r == IDresp.content for r in blacklistedrolesresp.content.split()]
            ) and any([r == IDresp.content for r in requiredrolesresp.content.split()]):
                await configmsg.delete()
                return await requiredrolesmsg.edit(
                    content=f"Unable to proceed: Cannot create a TSAR both blacklisted and required.",
                    delete_after=5,
                )
            content = f"Required roles: `{requiredrolesresp.content}`"
            if any([o == IDresp.content for o in requiredrolesresp.content.split()]):
                content += "\nYou specified the same Role ID, so this TSAR will be remove only."
            await requiredrolesmsg.edit(
                content=content,
                delete_after=5,
            )
            tsars[nameresp.content] = {
                "roleid": int(IDresp.content),
                "mindays": int(mindaysresp.content),
                "blacklisted": [int(r) for r in blacklistedrolesresp.content.split()]
                if blacklistedrolesresp.content.lower() != "none"
                else None,
                "required": [int(r) for r in requiredrolesresp.content.split()]
                if requiredrolesresp.content.lower() != "none"
                else None,
            }
            set_guildfile(ctx.guild.id, "tsar", json.dumps(tsars))
            return await configmsg.edit(
                content="TSAR list updated.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "❌":
            namemsg = await ctx.send(content="**Removing a TSAR.**\nName of this TSAR?")
            nameresp = await waitformsg()
            await namemsg.delete()
            del tsars[nameresp.content]
            set_guildfile(ctx.guild.id, "tsar", json.dumps(tsars))
            return await configmsg.edit(
                content="TSAR list updated.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "💣":
            confirmmsg = await ctx.send(content="Nuke the **ENTIRE** TSAR list?")
            confirmresp = await waitformsg()
            await confirmmsg.delete()
            if confirmresp.content.lower() == "yes":
                tsars = {}
                set_guildfile(ctx.guild.id, "tsar", json.dumps(tsars))
                return await configmsg.edit(
                    content="TSAR list nuked.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )
            else:
                return await configmsg.edit(
                    content="Aborted.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )


async def setup(bot):
    await bot.add_cog(TSAR(bot))
