import discord
from discord.ext import commands
import database
import assets

class Workshop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- RECETARIO (JUNK ARMOR SET) ---
        # Precios actualizados según tu configuración
        self.RECIPES = {
            "boots": {
                "name": "Junk Boots", 
                "slot": "boots",
                "cost_parts": 10, 
                "cost_money": 2000, 
                "def": 2, 
                "dur": 60, 
                "img": assets.IMAGES['armors']['junk_boots']
            },
            "helmet": {
                "name": "Junk Helmet", 
                "slot": "helmet",
                "cost_parts": 12, 
                "cost_money": 3500, 
                "def": 3, 
                "dur": 70, 
                "img": assets.IMAGES['armors']['junk_head']
            },
            "leggings": {
                "name": "Junk Leggings", 
                "slot": "leggings",
                "cost_parts": 16, 
                "cost_money": 4000, 
                "def": 4, 
                "dur": 90, 
                "img": assets.IMAGES['armors']['junk_legs']
            },
            "body": {
                "name": "Junk Body Armor", 
                "slot": "body",
                "cost_parts": 20, 
                "cost_money": 6000, 
                "def": 6, 
                "dur": 110, 
                "img": assets.IMAGES['armors']['junk_body']
            }
        }

        # ALIAS (Para que entienda español)
        self.ALIASES = {
            "botas": "boots", "pie": "boots", "boots": "boots", "pies": "boots",
            "casco": "helmet", "helmet": "helmet", "cabeza": "helmet",
            "pantalones": "leggings", "piernas": "leggings", "leggings": "leggings",
            "pechera": "body", "cuerpo": "body", "body": "body", "chest": "body", "pecho": "body"
        }

    # COMANDO: !craft <pieza> (Solo en LAB)
    @commands.command()
    async def craft(self, ctx, *, item_name: str = None):
        # 1. Verificar Canal usando configuración central
        if ctx.channel.id != self.bot.CHANNELS['lab']:
            msg = await ctx.send(f"❌ {ctx.author.mention}, ve al Taller en <#{self.bot.CHANNELS['lab']}>.")
            await ctx.message.delete()
            await msg.delete(delay=5)
            return

        if not item_name:
            await ctx.send("🛠️ **Sistema de Fabricación**\nUsa `!craft <pieza>` (Ej: `!craft botas`).\nConsulta los planos con `!recipes`.")
            return

        # 2. Normalizar nombre
        key = item_name.lower()
        if key in self.ALIASES:
            recipe_key = self.ALIASES[key]
        else:
            await ctx.send("❌ No reconozco ese plano. Usa `!recipes` para ver la lista.")
            return

        recipe = self.RECIPES[recipe_key]
        
        # 3. Intentar Fabricar (DB)
        resultado = database.perform_crafting(ctx.author.id, recipe['cost_parts'], recipe['cost_money'])

        if resultado == "OK":
            # Equipar automáticamente
            database.equip_armor(ctx.author.id, recipe["slot"], recipe["name"], recipe["def"], recipe["dur"])
            
            # Embed de Éxito
            embed = discord.Embed(title="¡Fabricación Exitosa!", color=0xff9900)
            embed.description = f"Has fabricado y equipado: **{recipe['name']}**"
            
            # Intentar poner imagen si existe en assets
            if recipe['img']:
                embed.set_thumbnail(url=recipe['img'])
            
            embed.add_field(name="Costos Pagados", value=f"⚙️ -{recipe['cost_parts']} Parts\n💎 -{recipe['cost_money']} Crystals", inline=True)
            embed.add_field(name="Estadísticas", value=f"🛡️ Def: +{recipe['def']}\n🔧 Dur: {recipe['dur']}", inline=True)
            
            await ctx.send(embed=embed)

        elif resultado == "NO_MONEY":
            await ctx.send(f"⚠️ **Fondos Insuficientes.**\nNecesitas: {recipe['cost_money']} 💎 E-Crystals.")
        
        elif resultado == "NO_PARTS":
            await ctx.send(f"⚠️ **Materiales Insuficientes.**\nNecesitas: {recipe['cost_parts']} ⚙️ Armor Parts.")
        
        else:
            await ctx.send("❌ Error desconocido en la base de datos.")

    # COMANDO: !recipes (Lista visual de precios)
    @commands.command(aliases=['recetas', 'planos'])
    async def recipes(self, ctx):
        if ctx.channel.id != self.bot.CHANNELS['lab'] and ctx.channel.id != self.bot.CHANNELS['database']:
             msg = await ctx.send(f"📜 Ve al laboratorio o base de datos para ver los planos.")
             await msg.delete(delay=3)
             return

        embed = discord.Embed(title="📜 Planos de Armadura (Junk Set)", description="Equipamiento básico de supervivencia.", color=0x00aaff)
        
        # Thumbnail de Armor Part desde Assets
        if 'armor_part' in assets.IMAGES['materials']:
            embed.set_thumbnail(url=assets.IMAGES['materials']['armor_part'])
        
        for key, r in self.RECIPES.items():
            info = f"🔩 **Coste:** `{r['cost_parts']} Parts` + `{r['cost_money']} 💎`\n"
            info += f"🛡️ **Stats:** `Def +{r['def']}` | `Dur {r['dur']}`"
            
            icono = "🪖" if key == "helmet" else "🛡️" if key == "body" else "👖" if key == "leggings" else "👢"
            
            embed.add_field(name=f"{icono} {r['name']}", value=info, inline=False)
        
        embed.set_footer(text="Usa !craft <nombre> en el Laboratorio.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Workshop(bot))