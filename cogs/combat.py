import discord
from discord.ext import commands
import random
import database 
import assets 
import datetime

class Combat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Diccionario para guardar estadísticas de la sesión actual (en memoria)
        # Formato: user_id: {start_time, xp, crystals, kills}
        self.active_missions = {} 

    # --- COMANDO: !start (Solo en Mission Zone) ---
    @commands.command()
    async def start(self, ctx):
        if ctx.channel.id != self.bot.CHANNELS['mission']:
            msg = await ctx.send(f"❌ Ve a <#{self.bot.CHANNELS['mission']}> para iniciar la inmersión.")
            await ctx.message.delete()
            await msg.delete(delay=5)
            return

        # Buscar el rol
        role = discord.utils.get(ctx.guild.roles, name=self.bot.MISSION_ROLE_NAME)
        if not role:
            return await ctx.send(f"⚠️ Error de Config: No encuentro el rol '{self.bot.MISSION_ROLE_NAME}' en el servidor.")

        # Asignar rol (Oculta otros canales)
        await ctx.author.add_roles(role)
        
        # Iniciar tracking de sesión
        self.active_missions[ctx.author.id] = {
            "start_time": datetime.datetime.now(),
            "xp_earned": 0,
            "crystals_earned": 0,
            "enemies_killed": 0
        }

        embed = discord.Embed(title="🚀 MISIÓN INICIADA", color=0xff0000)
        embed.description = "**Protocolo de Inmersión activado.**\nEl resto de la base ha sido bloqueada. Concéntrate en el objetivo.\n\nUsa `!attack` para combatir.\nUsa `!finish` para regresar a la base."
        embed.set_thumbnail(url=assets.IMAGES['ui']['start_mission'])
        await ctx.send(embed=embed)

    # --- COMANDO: !finish (Terminar Misión) ---
    @commands.command(aliases=['terminar', 'regresar'])
    async def finish(self, ctx):
        if ctx.channel.id != self.bot.CHANNELS['mission']:
            return

        # Quitar rol
        role = discord.utils.get(ctx.guild.roles, name=self.bot.MISSION_ROLE_NAME)
        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
        
        # Generar Reporte
        session = self.active_missions.pop(ctx.author.id, None)
        
        if session:
            duration = datetime.datetime.now() - session['start_time']
            mins = int(duration.total_seconds() / 60)
            seconds = int(duration.total_seconds() % 60)
            
            # Crear Embed de Reporte
            embed = discord.Embed(title="📊 REPORTE DE MISIÓN", color=0x00ff00)
            embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
            embed.add_field(name="Hunter", value=ctx.author.name, inline=True)
            embed.add_field(name="Duración", value=f"{mins}m {seconds}s", inline=True)
            embed.add_field(name="Bajas", value=str(session['enemies_killed']), inline=True)
            embed.add_field(name="Recursos Obtenidos", value=f"💎 {session['crystals_earned']} | XP {session['xp_earned']}", inline=False)
            embed.set_footer(text="Datos guardados en Hunter Database.")

            # Enviar al canal DATABASE y al usuario
            db_channel = self.bot.get_channel(self.bot.CHANNELS['database'])
            if db_channel:
                await db_channel.send(content=ctx.author.mention, embed=embed)
            
            await ctx.send("✅ Misión finalizada. Revisa el reporte en la Base de Datos.")
        else:
            await ctx.send("✅ Protocolo finalizado.")

    # --- COMANDO: !attack (Restringido) ---
    @commands.command(aliases=['x-buster', 'disparar'])
    @commands.cooldown(1, 3, commands.BucketType.user) 
    async def attack(self, ctx):
        # SOLO PERMITIDO EN: Simulación, Boss, Misión
        allowed = [self.bot.CHANNELS['simulation'], self.bot.CHANNELS['boss'], self.bot.CHANNELS['mission']]
        if ctx.channel.id not in allowed:
            await ctx.message.delete()
            msg = await ctx.send(f"❌ Combate no permitido aquí.")
            await msg.delete(delay=3)
            return

        # Datos del Jugador
        data = database.get_hunter_data(ctx.author.id)
        if not data:
            database.register_hunter(ctx.author.id)
            data = database.get_hunter_data(ctx.author.id)

        current_hp = data[5]
        max_hp = data[6]
        level = data[3]
        
        if current_hp <= 0:
            embed = discord.Embed(title="⚠️ SISTEMAS CRÍTICOS", color=0x000000)
            embed.description = f"{ctx.author.mention}, estás **ABATIDO**.\nUsa un **Sub-Tank** (`!use Sub-Tank`) para reiniciar sistemas."
            embed.set_thumbnail(url=assets.IMAGES['ui']['warning'])
            await ctx.send(embed=embed)
            return

        # --- CÁLCULO DE BUFFS ---
        buffs = database.get_active_buffs(ctx.author.id)
        atk_mult = 1.0
        def_mult = 1.0
        regen_amount = 0
        active_buffs_msg = ""
        
        for b_type, b_mult, b_end in buffs:
            if b_type == 'atk': 
                atk_mult = b_mult
                active_buffs_msg += " `[⚔️ ATK UP]`"
            elif b_type == 'def': 
                def_mult = b_mult
                active_buffs_msg += " `[🛡️ DEF UP]`"
            elif b_type == 'regen':
                regen_amount = int(b_mult)

        # Regeneración pasiva
        if regen_amount > 0 and current_hp < max_hp:
             database.modify_hp(ctx.author.id, regen_amount)
             active_buffs_msg += f" `[💚 +{regen_amount} HP]`"

        # --- LÓGICA DE COMBATE ---
        xp_gain = 0
        crystal_gain = 0
        parts_gain = 0
        msg_loot = ""
        user_def = database.get_total_defense(ctx.author.id) * def_mult 

        # ---------------------------------------------------------------------
        # ZONA 1: MISIÓN (TRACKING ACTIVO)
        # ---------------------------------------------------------------------
        if ctx.channel.id == self.bot.CHANNELS['mission']:
            enemy_name, enemy_img = random.choice(list(assets.IMAGES['enemies'].items()))
            
            critico = random.randint(1, 10)
            base_dmg = random.randint(20, 40) + (level * 2)
            player_dmg = int(base_dmg * atk_mult)
            if critico == 10: player_dmg *= 2
            
            base_enemy_atk = random.randint(10, 25)
            damage_received = max(1, int(base_enemy_atk - user_def))
            
            new_hp = database.update_hunter_stats(ctx.author.id, hp_change=-damage_received)
            database.damage_equipment(ctx.author.id)
            
            embed = discord.Embed(color=0xff9900)
            embed.set_thumbnail(url=enemy_img)
            
            desc = f"⚔️ **{enemy_name.replace('_', ' ').title()}** detectado.{active_buffs_msg}\n"
            desc += f"💥 Disparo: **{player_dmg}** daño.\n"
            
            if new_hp <= 0:
                desc += f"\n💀 **¡DERROTADO!** Recibiste {damage_received} daño letal."
                embed.color = 0x2f3136
                embed.set_image(url=assets.IMAGES['ui']['warning'])
            else:
                desc += f"🛡️ Daño recibido: **-{damage_received}** (Def: {int(user_def)})\n"
                
                xp_gain = random.randint(10, 25)
                crystal_gain = random.randint(5, 15)
                parts_gain = random.randint(1, 3)
                
                # Drop Raro
                if random.random() < 0.2:
                    heal = 20
                    new_hp = database.update_hunter_stats(ctx.author.id, hp_change=heal)
                    msg_loot += f"\n💚 **¡Life Energy!** +{heal} HP."
                    embed.set_footer(text="Item recuperado", icon_url=assets.IMAGES['consumables']['life_energy_small'])

                desc += f"\n🏆 **VICTORIA**\n`+{xp_gain} XP` | `+{crystal_gain} 💎` | `+{parts_gain} ⚙️`{msg_loot}"
                
                # --- ACTUALIZAR TRACKING DE MISIÓN ---
                if ctx.author.id in self.active_missions:
                    self.active_missions[ctx.author.id]['xp_earned'] += xp_gain
                    self.active_missions[ctx.author.id]['crystals_earned'] += crystal_gain
                    self.active_missions[ctx.author.id]['enemies_killed'] += 1

            embed.description = desc

        # ---------------------------------------------------------------------
        # ZONA 2: BOSS
        # ---------------------------------------------------------------------
        elif ctx.channel.id == self.bot.CHANNELS['boss']:
            boss_data = database.get_boss()
            if boss_data and boss_data[4] == 1:
                base_dmg = random.randint(50, 100)
                dano = int(base_dmg * atk_mult)
                boss_hp_new = database.damage_boss(dano)
                
                boss_atk = random.randint(30, 60)
                damage_received = max(5, int(boss_atk - user_def))
                new_hp = database.update_hunter_stats(ctx.author.id, hp_change=-damage_received)
                database.damage_equipment(ctx.author.id)
                
                xp_gain = dano
                
                embed = discord.Embed(description=f"⚔️ **BOSS BATTLE** {active_buffs_msg}", color=0xff0000)
                embed.add_field(name="Ataque", value=f"Golpeaste por **{dano} HP**.", inline=False)
                
                if new_hp <= 0:
                    embed.add_field(name="Estado", value=f"💀 **ABATIDO** (-{damage_received} HP).", inline=False)
                else:
                    embed.add_field(name="Estado", value=f"🛡️ Recibes **-{damage_received} HP**.", inline=False)
                
                if boss_hp_new <= 0:
                    embed.description += f"\n\n🏆 **¡BOSS ELIMINADO!**"
                    embed.color = 0xd4af37
                
                embed.set_thumbnail(url=boss_data[3])
                embed.set_footer(text=f"Boss HP: {max(0, boss_hp_new)} / {boss_data[1]}")
            else:
                await ctx.send("❌ No hay Boss activo.")
                return
        
        # ---------------------------------------------------------------------
        # ZONA 3: SIMULACIÓN
        # ---------------------------------------------------------------------
        else:
            xp_gain = 10
            new_hp = current_hp
            embed = discord.Embed(description=f"💥 **Simulación:** +{xp_gain} XP {active_buffs_msg}", color=0x00ff00)
            if random.randint(1, 10) == 10:
                embed.set_image(url="https://i.ibb.co/HpXRg8XR/shottcritico.gif")

        # GUARDAR DATOS Y CHECK LEVEL UP
        if xp_gain > 0 and new_hp > 0:
            database.update_hunter_stats(ctx.author.id, xp_change=xp_gain, money_change=crystal_gain, parts_change=parts_gain)
            
            new_data = database.get_hunter_data(ctx.author.id)
            if new_data[1] >= level * 100:
                new_lvl = level + 1
                new_max = 100 + (new_lvl * 10)
                database.update_stats(ctx.author.id, new_lvl, new_max)
                database.modify_hp(ctx.author.id, new_max)
                embed.description += f"\n🆙 **LEVEL UP!** Nivel {new_lvl} | HP {new_max}"
                embed.color = 0x00ffff

        if ctx.channel.id != self.bot.CHANNELS['boss']:
            icon_hp = "💚" if new_hp > (max_hp * 0.3) else "❤️"
            embed.set_footer(text=f"{icon_hp} HP: {new_hp}/{max_hp} | 🛡️ Def: {int(user_def)}")

        await ctx.send(embed=embed)

    # --- COMANDO: !rank (Solo en Rank Board) ---
    @commands.command(aliases=['ranking', 'top'])
    async def rank(self, ctx):
        if ctx.channel.id != self.bot.CHANNELS['rank']:
            msg = await ctx.send(f"🏆 Ver ranking en <#{self.bot.CHANNELS['rank']}>.")
            await ctx.message.delete()
            await msg.delete(delay=5)
            return

        conn = database.get_connection()
        c = conn.cursor()
        c.execute("SELECT user_id, level, rank FROM hunters ORDER BY level DESC LIMIT 10")
        top_hunters = c.fetchall()
        conn.close()

        embed = discord.Embed(title="🏆 TOP HUNTERS - RANKING GLOBAL", color=0xd4af37)
        desc = ""
        for i, (uid, lvl, rnk) in enumerate(top_hunters, 1):
            user = self.bot.get_user(uid)
            name = user.name if user else "Unknown Hunter"
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            desc += f"**{medal} {name}** — Rango {rnk} (Lvl {lvl})\n"
        
        embed.description = desc
        await ctx.send(embed=embed)

    # --- STATUS ---
    @commands.command(aliases=['perfil', 'stats'])
    async def status(self, ctx):
        # Permitido en: Database, Sim, Mission, Lab, Rank
        allowed = [
            self.bot.CHANNELS['database'], self.bot.CHANNELS['simulation'], 
            self.bot.CHANNELS['mission'], self.bot.CHANNELS['lab'], self.bot.CHANNELS['rank']
        ]
        if ctx.channel.id not in allowed:
            await ctx.message.delete()
            return

        data = database.get_hunter_data(ctx.author.id)
        if not data: return
        
        # Calcular XP para siguiente nivel
        xp_next = data[3] * 100
        
        embed = discord.Embed(title=f"Tarjeta de Hunter: {ctx.author.name}", color=0x0000ff)
        embed.add_field(name="Rango", value=data[4], inline=True)
        embed.add_field(name="Nivel", value=str(data[3]), inline=True)
        embed.add_field(name="HP", value=f"{data[5]} / {data[6]}", inline=True)
        embed.add_field(name="DNA Souls (XP)", value=f"{data[1]} / {xp_next}", inline=True)
        
        if ctx.author.avatar:
            embed.set_thumbnail(url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    # --- ERROR HANDLER ---
    @attack.error
    async def attack_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.message.delete()
            msg = await ctx.send(f"⏳ Recargando... {error.retry_after:.1f}s")
            await msg.delete(delay=2)

async def setup(bot):
    await bot.add_cog(Combat(bot))