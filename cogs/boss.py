import discord
from discord.ext import commands, tasks
import database
import random
import asyncio

class Boss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Iniciamos el bucle automático de jefes
        self.boss_loop.start()

    # BUCLE DE SPAWN AUTOMÁTICO
    # Se ejecuta cada 1 hora para verificar si aparece un jefe
    @tasks.loop(hours=1)
    async def boss_loop(self):
        # Probabilidad de aparición: 20% cada hora
        # Esto asegura aprox 4-5 jefes al día de forma aleatoria
        if random.random() < 0.20:
            channel = self.bot.get_channel(self.bot.CHANNELS['boss'])
            if not channel: return

            # Lista de posibles Jefes (Nombre, HP, URL)
            bosses = [
                ("Vile", 5000, "https://www.spriters-resource.com/media/asset_icons/152/155164.gif"),
                ("Sigma", 8000, "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/e6be3206-5bc7-4ad3-b2b0-009d5a10200f/d28n1v3-d12e200e-43ef-4dfe-ac6b-aeee252c23ad.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiIvZi9lNmJlMzIwNi01YmM3LTRhZDMtYjJiMC0wMDlkNWExMDIwMGYvZDI4bjF2My1kMTJlMjAwZS00M2VmLTRkZmUtYWM2Yi1hZWVlMjUyYzIzYWQuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.4UUioIQWg7X-54GCZVEMebBsLF7HsGJrYiFp-CCQoJA"),
                ("Magma Dragoon", 6000, "https://i.pinimg.com/originals/91/17/a9/9117a9ebdd32e32a491e8e33401af70d.gif"),
                ("Toxic Seahorse", 5000, "https://i.ibb.co/jN5cNw7/toxicseahorse.gif"),
                ("Dark Necrobat", 4500, "https://cdn.megamanwiki.com/b/b7/MMX5_-_Dark_Necrobat_Sprite.gif")
            ]
            
            # Elegir uno al azar
            name, hp, url = random.choice(bosses)

            # Spawnear en la Base de Datos
            database.spawn_boss(name, hp, url)
            
            # Anuncio Épico
            embed = discord.Embed(title="🚨 ALERTA DE VIRUS SIGMA 🚨", color=0xff0000)
            embed.description = f"**{name}** ha aparecido en el sector.\nHP: {hp}\n¡Todas las unidades al combate! Usen `!attack`."
            embed.set_image(url=url)
            embed.set_footer(text="Nivel de Amenaza: MAVERICK")
            
            await channel.send(content="@everyone", embed=embed)

    # Esperar a que el bot esté listo antes de iniciar el bucle
    @boss_loop.before_loop
    async def before_boss_loop(self):
        await self.bot.wait_until_ready()

    # COMANDO MANUAL (Solo Admins)
    # Útil si quieres forzar un evento o probar el sistema
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spawn(self, ctx, nombre: str, hp: int, url: str = None):
        if ctx.channel.id != self.bot.CHANNELS['boss']:
            return await ctx.send(f"❌ Usa este comando en <#{self.bot.CHANNELS['boss']}>.")

        if not url:
            # URL por defecto (Warning)
            url = "https://i.ibb.co/Nn95B12d/warning.gif"

        database.spawn_boss(nombre, hp, url)
        
        embed = discord.Embed(title="🚨 MAVERICK DETECTADO (MANUAL) 🚨", color=0xff0000)
        embed.description = f"**{nombre}** ha aparecido con **{hp} HP**.\n¡Hunters, ataquen con `!attack`!"
        embed.set_image(url=url)
        
        await ctx.send(content="@everyone", embed=embed)
        await ctx.message.delete() # Borrar el comando del admin para limpieza

async def setup(bot):
    await bot.add_cog(Boss(bot))