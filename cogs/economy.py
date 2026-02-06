import discord
from discord.ext import commands
import database
import assets 

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # CATÁLOGO DE PRECIOS (Personalizados)
        self.shop_items = {
            "Sub-Tank": 2000,        
            "Armor Part": 700,       
            "Power Chip S": 300,    
            "Defense Chip S": 300,  
            "Speed Chip": 300,      
            "Regen Chip": 2000      
        }

    # --- COMANDO: !shop (Solo en LAB) ---
    @commands.command()
    async def shop(self, ctx):
        # VERIFICACIÓN DE CANAL
        if ctx.channel.id != self.bot.CHANNELS['lab']:
            msg = await ctx.send(f"❌ {ctx.author.mention}, ve al Laboratorio en <#{self.bot.CHANNELS['lab']}>.")
            await ctx.message.delete()
            await msg.delete(delay=5)
            return

        data = database.get_hunter_data(ctx.author.id) 
        saldo = data[2] if data else 0

        embed = discord.Embed(title="🛒 Laboratorio del Dr. Light", color=0x00ff00)
        embed.description = f"Bienvenido, Hunter.\n**Saldo:** {saldo} E-Crystals\nUsa `!buy <item>` para adquirir suministros."
        
        # Imágenes desde assets.py
        if 'shop_keeper' in assets.IMAGES['ui']:
            embed.set_thumbnail(url=assets.IMAGES['ui']['shop_keeper'])
        if 'shop_bg' in assets.IMAGES['ui']:
            embed.set_image(url=assets.IMAGES['ui']['shop_bg']) 
        
        lista_texto = ""
        for item, price in self.shop_items.items():
            icon = "🔹"
            if "Chip" in item: icon = "💾"
            elif "Tank" in item: icon = "💊"
            elif "Part" in item: icon = "⚙️"
            lista_texto += f"{icon} **{item}** — 💎 `{price}`\n"
            
        embed.add_field(name="Suministros:", value=lista_texto, inline=False)
        embed.set_footer(text="Sumi System", icon_url=assets.IMAGES['currency']['e_crystal'])
        await ctx.send(embed=embed)

    # --- COMANDO: !buy (Solo en LAB) ---
    @commands.command()
    async def buy(self, ctx, *, item_name: str = None):
        if ctx.channel.id != self.bot.CHANNELS['lab']:
            return # Ignoramos silenciosamente si no es el lab

        if not item_name:
            await ctx.send("❌ Ej: `!buy Sub-Tank`")
            return

        item_real = None
        precio = 0
        for p_item, p_price in self.shop_items.items():
            if p_item.lower() == item_name.lower():
                item_real = p_item
                precio = p_price
                break
        
        if not item_real:
            await ctx.send("❌ Objeto no encontrado en el catálogo.")
            return

        exito = database.purchase_item(ctx.author.id, precio, item_real)
        if exito:
            embed = discord.Embed(title="¡Compra Exitosa!", description=f"Obtuviste: **{item_real}**", color=0xffff00)
            await ctx.send(embed=embed)
        else:
            data = database.get_hunter_data(ctx.author.id)
            saldo = data[2] if data else 0
            await ctx.send(f"⚠️ **Fondos insuficientes.** Tienes: {saldo} 💎")

    # --- COMANDO: !inventory (Multicanal) ---
    @commands.command(aliases=['bag', 'mochila', 'inv'])
    async def inventory(self, ctx):
        # PERMITIDO EN: Lab, Database, Sim, Mission
        allowed = [
            self.bot.CHANNELS['lab'], 
            self.bot.CHANNELS['database'], 
            self.bot.CHANNELS['simulation'], 
            self.bot.CHANNELS['mission']
        ]
        
        if ctx.channel.id not in allowed:
            await ctx.message.delete()
            msg = await ctx.send("❌ Aquí no puedes abrir la mochila.")
            await msg.delete(delay=3)
            return

        items = database.get_inventory(ctx.author.id)
        data = database.get_hunter_data(ctx.author.id)
        crystals = data[2] if data else 0
        parts = data[7] if data else 0

        embed = discord.Embed(title=f"🎒 Inventario de {ctx.author.name}", color=0xff9900)
        embed.add_field(name="Recursos", value=f"💎 **E-Crystals:** {crystals}\n⚙️ **Parts:** {parts}", inline=False)

        if items:
            texto_items = ""
            for item, cantidad in items:
                texto_items += f"📦 **{item}**: x{cantidad}\n"
            embed.add_field(name="Mochila", value=texto_items, inline=False)
        else:
            embed.add_field(name="Mochila", value="*Vacía*", inline=False)
        await ctx.send(embed=embed)

    # --- COMANDO: !use (Multicanal de acción) ---
    @commands.command()
    async def use(self, ctx, *, item_name: str = None):
        # PERMITIDO EN: Lab, Sim, Mission
        allowed = [
            self.bot.CHANNELS['lab'], 
            self.bot.CHANNELS['simulation'], 
            self.bot.CHANNELS['mission']
        ]
        
        if ctx.channel.id not in allowed:
            await ctx.message.delete()
            return 

        if not item_name:
            await ctx.send("❌ Dime qué usar. Ej: `!use Sub-Tank`")
            return

        # Normalizar nombre
        item_real = None
        for p_item in self.shop_items.keys():
            if p_item.lower() == item_name.lower():
                item_real = p_item
                break
        
        if not item_real:
            await ctx.send("❌ No reconoces ese objeto.")
            return

        # Intentar consumir y aplicar efecto
        if database.consume_item(ctx.author.id, item_real):
            embed = discord.Embed(color=0x00ff00)
            
            if "Sub-Tank" in item_real:
                database.modify_hp(ctx.author.id, 1000) # Cura total
                embed.title = "❤️ ¡Sub-Tank Activado!"
                embed.description = "Tus PV han sido restaurados al máximo."
                if 'subtank' in assets.IMAGES['consumables']:
                    embed.set_thumbnail(url=assets.IMAGES['consumables']['subtank'])
            
            elif "Power Chip S" in item_real:
                database.activate_buff(ctx.author.id, 'atk', 1.2, 60) 
                embed.title = "⚔️ Power Chip S Activado"
                embed.description = "Daño aumentado un **20%** por 60 segundos."
                if 'atk_s' in assets.IMAGES['chips']:
                    embed.set_thumbnail(url=assets.IMAGES['chips']['atk_s'])

            elif "Defense Chip S" in item_real:
                database.activate_buff(ctx.author.id, 'def', 1.2, 60) 
                embed.title = "🛡️ Defense Chip S Activado"
                embed.description = "Defensa aumentada un **20%** por 60 segundos."
                if 'def_s' in assets.IMAGES['chips']:
                    embed.set_thumbnail(url=assets.IMAGES['chips']['def_s'])
            
            elif "Regen Chip" in item_real:
                 database.activate_buff(ctx.author.id, 'regen', 5, 30) 
                 embed.title = "💚 Auto-Repair System Online"
                 embed.description = "Regeneración activada: +5 HP por turno."
                 if 'regen_chip' in assets.IMAGES['chips']:
                    embed.set_thumbnail(url=assets.IMAGES['chips']['regen_chip'])

            else:
                embed.description = f"Usaste **{item_real}**, pero no tuvo efecto visible."

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"⚠️ No tienes **{item_real}** en tu inventario.")

async def setup(bot):
    await bot.add_cog(Economy(bot))