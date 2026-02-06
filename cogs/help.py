import discord
from discord.ext import commands
import assets

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Quitamos el comando help por defecto si aún existe
        self.bot.remove_command('help')

    @commands.command(aliases=['ayuda', 'manual'])
    async def help(self, ctx):
        # FILTRO POR CANAL: Muestra la ayuda relevante para DONDE estás
        
        embed = discord.Embed(title="📘 SISTEMA DE AYUDA MAVERICK", color=0x00aaff)
        
        # Usamos la imagen de Douglas o el Dr. Light para darle personalidad
        if 'shop_keeper' in assets.IMAGES['ui']:
            embed.set_thumbnail(url=assets.IMAGES['ui']['shop_keeper'])

        # 1. AYUDA EN BASE DE DATOS
        if ctx.channel.id == self.bot.CHANNELS['database']:
            embed.description = "**Comandos disponibles en BASE DE DATOS:**\n*Centro de información y gestión de recursos.*"
            embed.add_field(name="📋 Información", value="`!status` - Ver perfil de Hunter\n`!bag` - Ver inventario y recursos\n`!recipes` - Ver planos de armadura\n`!help` - Mostrar este manual")
        
        # 2. AYUDA EN SIMULACIÓN
        elif ctx.channel.id == self.bot.CHANNELS['simulation']:
            embed.description = "**Comandos disponibles en SIMULACIÓN:**\n*Zona de entrenamiento seguro. Sin riesgo.*"
            embed.add_field(name="⚔️ Acción", value="`!attack` - Entrenar (Ganas poca XP)\n`!use <item>` - Usar objetos")
            embed.add_field(name="📋 Info", value="`!status`, `!bag`, `!help`")

        # 3. AYUDA EN ZONA DE MISIÓN
        elif ctx.channel.id == self.bot.CHANNELS['mission']:
            embed.description = "**Comandos disponibles en ZONA DE MISIÓN:**\n*¡ALERTA! Enemigos reales. Daño letal activo.*"
            embed.add_field(name="🚀 Operaciones", value="`!start` - Iniciar inmersión (Oculta otros canales)\n`!finish` - Terminar misión y generar reporte")
            embed.add_field(name="⚔️ Combate", value="`!attack` - Combatir (Loot habilitado)\n`!use <item>` - Usar objetos de soporte")

        # 4. AYUDA EN LABORATORIO
        elif ctx.channel.id == self.bot.CHANNELS['lab']:
            embed.description = "**Comandos disponibles en LABORATORIO:**\n*Tienda y Taller de Ingeniería.*"
            embed.add_field(name="🛒 Tienda", value="`!shop` - Ver catálogo\n`!buy <item>` - Comprar suministros")
            embed.add_field(name="🛠️ Taller", value="`!craft <pieza>` - Fabricar armaduras\n`!recipes` - Ver lista de planos")
            embed.add_field(name="📋 Info", value="`!bag`, `!status`, `!use`")

        # 5. AYUDA EN RANK BOARD
        elif ctx.channel.id == self.bot.CHANNELS['rank']:
             embed.description = "**Comandos disponibles en RANK BOARD:**\n*Salón de la Fama.*"
             embed.add_field(name="🏆 Ranking", value="`!rank` - Ver Top Hunters\n`!status` - Ver tu tarjeta personal")

        # 6. AYUDA EN BOSS RAID
        elif ctx.channel.id == self.bot.CHANNELS['boss']:
             embed.description = "**Comandos disponibles en ZONA DE ALERTA:**\n*¡PELIGRO EXTREMO! Jefe Maverick detectado.*"
             embed.add_field(name="⚔️ Combate", value="`!attack` - Atacar al Jefe\n`!use <item>` - Usar objetos de emergencia")
             
        # CASO POR DEFECTO (Canal no configurado)
        else:
            embed.description = "❌ Este canal no tiene funciones del sistema Hunter.\nPor favor, dirígete a uno de los canales oficiales:\n\n<#{}> - Misiones\n<#{}> - Laboratorio\n<#{}> - Base de Datos".format(
                self.bot.CHANNELS['mission'], 
                self.bot.CHANNELS['lab'],
                self.bot.CHANNELS['database']
            )

        embed.set_footer(text="Escribe el comando exacto para interactuar.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))