import discord
import os
import asyncio
from discord.ext import commands
import database
from dotenv import load_dotenv
from threading import Thread 
from flask import Flask      

# Cargar variables de entorno (busca el archivo .env si estás en tu PC)
load_dotenv()

# 1. Configuración del Bot y Permisos
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# --- MINI SERVIDOR WEB PARA RENDER (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "¡Bot Maverick Hunter activo y operando!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --------------------------------------------------

# --- CONFIGURACIÓN CENTRAL DE CANALES (IDs) ---
bot.CHANNELS = {
    "database": 1469181782976102442,   
    "simulation": 1469181844951011510, 
    "mission": 1469418192609874064,    
    "lab": 1469181934105006152,        
    "boss": 1469181984353026142,       
    "rank": 1469182027948359680        
}

# Configuración del Rol para el Modo Misión
bot.MISSION_ROLE_NAME = "En misión" 

# 2. Función para cargar las extensiones (Cogs)
async def load_extensions():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f"📥 Extensión cargada: {filename}")
                except Exception as e:
                    print(f"❌ Error cargando {filename}: {e}")
    else:
        print("⚠️ La carpeta 'cogs' no existe.")

# 3. Evento de arranque
@bot.event
async def on_ready():
    database.init_db()
    print('-----------------------------------------')
    print(f'✅ Sistema Principal en línea: {bot.user.name}')
    print(f'🆔 ID: {bot.user.id}')
    print('-----------------------------------------')
    print('📡 VERIFICACIÓN DE CANALES CONFIGURADOS:')
    for name, id_channel in bot.CHANNELS.items():
        print(f"   🔹 {name.upper()}: {id_channel}")
    print('-----------------------------------------')

# 4. Ejecución Asíncrona
async def main():
    async with bot:
        await load_extensions()
        
        # --- SEGURIDAD: LEER TOKEN DE VARIABLE DE ENTORNO ---
        token = os.getenv('DISCORD_TOKEN')
        
        if not token:
            print("❌ ERROR FATAL: No se encontró el token.")
            print("Asegúrate de configurar la variable DISCORD_TOKEN en Render o en tu archivo .env")
            return
            
        await bot.start(token)

if __name__ == '__main__':
    keep_alive() 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot apagado manualmente.")
