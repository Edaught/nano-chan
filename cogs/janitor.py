"""
This cog is to be used primarily for small janitorial tasks 
(removing clover once member is hit, pruning clovers)
"""
from discord import AuditLogAction
from discord.ext import commands
from .utils import checks
from datetime import datetime, timedelta
import asyncio

class Janitor():
    """
    The main class wrapepr
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        try:
            self.bg_task = self.bot.loop.create_task(self.daily_prune())
        except Exception as e:
            self.bot.logger.warning(f'Error starting task prune_clovers: {e}')
    
    def remove_clover(self, member) -> list:
        member_roles = member.roles
        for index, role in enumerate(member_roles):
            if role.name.lower() == 'clover':
                clover_index = index
        del member_roles[clover_index]
        return member_roles

    async def on_message(self, message):
        if message.author.bot:
            return
        has_clover = False
        clover_index = None
        has_member = False
        member_roles = message.author.roles
        for index, role in enumerate(member_roles):
            if role.name.lower() == 'clover':
                has_clover = True
            elif role.name.lower() == 'member':
                has_member = True
        if message.channel.id in self.bot.filter_channels:
            if message.content.lower() == '.iam clover':
                await self.add_clover(message, has_member)
            return
        if has_clover and has_member:
            member_roles = self.remove_clover(message.author)
            try:
                await message.author.edit(
                    roles=member_roles,
                    reason="User upgraded from clover to member")
                await message.add_reaction('🎊')
                self.bot.logger.info(
                    f'{message.author.display_name} was just promoted to member!')
            except Exception as e:
                self.bot.logger.warning(f'Error updating users roles: {e}')

    @commands.command(hidden=True)
    @checks.has_permissions(manage_roles=True)
    async def prune(self, ctx):
        await self.prune_clovers()

    @prune.error
    async def prune_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            self.bot.logger.warning(f'{ctx.message.author} tried to run prune w/o permissions')

    async def daily_prune(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Starting prune task, first prune in 24 hours")
        while not self.bot.is_closed():
            await asyncio.sleep(86400)
            await self.prune_clovers()

    async def add_clover(self, message, has_member):
        if has_member:
            return
        a_irl = self.bot.get_guild(self.bot.guild_id) # a_irl guild id
        for role in a_irl.roles:
            if role.name.lower() == 'clover':
                clover_role = role
        if not clover_role:
            self.bot.logger.warning(
                f'Something went really wrong, I couldn\'t find the clover role')
            return
        member_roles = message.author.roles
        member_roles.append(clover_role)
        try:
            await message.author.edit(
                roles=member_roles,
                reason=f'Self-applied role in #welcome-center'
            )
            self.bot.logger.info(
                f'Successfully applied clover to {message.author.display_name}')
            await message.delete()
        except Exception as e:
            self.bot.logger.warning(
                f'Error applying role to {message.author.display_name}: {e}')
        return


    async def prune_clovers(self):
        self.bot.logger.info('Starting prune task now')
        safe_users = []
        clovers = []
        clover_role = None
        mod_log = self.bot.get_channel(self.bot.mod_log)
        dt_24hr = datetime.utcnow() - timedelta(days=1)
        a_irl = self.bot.get_guild(self.bot.guild_id) # a_irl guild id
        for role in a_irl.roles:
            if role.name.lower() == 'clover':
                clover_role = role
        if not clover_role:
            self.bot.logger.warning(
                f'Something went really wrong, I couldn\'t find the clover role')
            return
        clovers = clover_role.members
        audit_logs = a_irl.audit_logs(
            after=dt_24hr,
            action=AuditLogAction.member_role_update)
        async for entry in audit_logs:
            if entry.created_at > dt_24hr:
                for role in entry.after.roles:
                    if role.name.lower() == 'clover':
                        if entry.target.id not in safe_users:
                            safe_users.append(entry.target.id)
        prune_info = {'pruned': False, 'amount': 0}
        for member in clovers:
            if member.id not in safe_users:
                try:
                    new_roles = self.remove_clover(member)
                    await member.edit(
                        roles=new_roles,
                        reason="Pruned due to inactivity"
                    )
                    prune_info['pruned'] = True
                    prune_info['amount'] += 1
                except Exception as e:
                    self.bot.logger.warning(
                        f'Error pruning clovers: {e}'
                    )
        self.bot.logger.info(f'Prune info: {prune_info}')
        if prune_info['pruned']:
            try:
                await mod_log.send(f'Pruned {prune_info["amount"]} clovers ✂️🍀')
            except Exception as e:
                self.bot.logger.warning(f'Error posting prune info to mod_log: {e}')
