import discord
import os
import asyncio
from discord.ext import commands
import database
from threading import Thread # <--- NUEVO: Para el servidor web
from flask import Flask      # <--- NUEVO: Para el servidor web

# 1. Configuración del Bot y Permisos
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True # NECESARIO para que el bot pueda dar y quitar roles (Modo Misión)

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
# El bot usará estos IDs para saber dónde permitir cada comando.
bot.CHANNELS = {
    "database": 1469181782976102442,   # ID del canal #hunter-database
    "simulation": 1469181844951011510, # ID del canal #simulation-room
    "mission": 1469418192609874064,    # ID del canal #mission-zone
    "lab": 1469181934105006152,        # ID del canal #hunter-lab
    "boss": 1469181984353026142,       # ID del canal #sigma-virus-alert
    "rank": 1469182027948359680        # ID del canal #rank-board
}

# Configuración del Rol para el Modo Misión
bot.MISSION_ROLE_NAME = "En misión" 

# 2. Función para cargar las extensiones (Cogs) automáticamente
async def load_extensions():
    # Busca archivos .py en la carpeta 'cogs'
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
    # Inicializar la base de datos al encender
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
        # TU TOKEN (Ya incluido)
        await bot.start('MTQ2OTE4NTgzMjE5NDgwNTc4MA.GYuzL2.5urj_7rCmbd1CARHs7C9vEOGIPzqsrSbhByDRw')

if __name__ == '__main__':
    keep_alive() # <--- ARRANCA EL SERVIDOR WEB ANTES QUE EL BOT
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot apagado manualmente.")