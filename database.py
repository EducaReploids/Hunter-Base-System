import sqlite3
import time # NUEVO: Necesario para controlar el tiempo de los chips

def get_connection():
    return sqlite3.connect("hunter_base.db")

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. HUNTERS V2
    c.execute('''CREATE TABLE IF NOT EXISTS hunters (
                    user_id INTEGER PRIMARY KEY,
                    dna_souls INTEGER DEFAULT 0,
                    e_crystals INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    rank TEXT DEFAULT 'E',
                    current_hp INTEGER DEFAULT 100,
                    max_hp INTEGER DEFAULT 100,
                    armor_parts INTEGER DEFAULT 0
                )''')
    
    # 2. INVENTARIO
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    item_name TEXT,
                    quantity INTEGER,
                    PRIMARY KEY (user_id, item_name)
                )''')

    # 3. EQUIPAMIENTO
    c.execute('''CREATE TABLE IF NOT EXISTS equipment (
                    user_id INTEGER,
                    slot TEXT, 
                    item_name TEXT,
                    defense INTEGER,
                    current_durability INTEGER,
                    max_durability INTEGER,
                    PRIMARY KEY (user_id, slot)
                )''')

    # 4. ACTIVE BUFFS (Chips)
    c.execute('''CREATE TABLE IF NOT EXISTS active_buffs (
                    user_id INTEGER,
                    buff_type TEXT,    -- 'atk', 'def', 'spd'
                    multiplier REAL,   -- ej: 1.5
                    end_time REAL,     -- Timestamp fin
                    PRIMARY KEY (user_id, buff_type)
                )''')

    # 5. JEFE ACTIVO
    c.execute('''CREATE TABLE IF NOT EXISTS active_boss (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT,
                    max_hp INTEGER,
                    current_hp INTEGER,
                    image_url TEXT,
                    active INTEGER DEFAULT 0
                )''')

    conn.commit()
    conn.close()
    print("💾 Base de Datos vFinal (RPG System) Inicializada.")

# --- FUNCIONES DE JUGADOR ---

def register_hunter(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO hunters (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_hunter_data(user_id):
    conn = get_connection()
    c = conn.cursor()
    register_hunter(user_id)
    c.execute("SELECT * FROM hunters WHERE user_id = ?", (user_id,))
    data = c.fetchone()
    conn.close()
    return data 

def update_hunter_stats(user_id, hp_change=0, xp_change=0, money_change=0, parts_change=0):
    conn = get_connection()
    c = conn.cursor()
    register_hunter(user_id)
    
    c.execute("SELECT current_hp, max_hp FROM hunters WHERE user_id = ?", (user_id,))
    stats = c.fetchone()
    cur_hp, max_hp = stats[0], stats[1]
    
    new_hp = cur_hp + hp_change
    if new_hp > max_hp: new_hp = max_hp
    if new_hp < 0: new_hp = 0
    
    c.execute('''UPDATE hunters 
                 SET current_hp = ?, 
                     dna_souls = dna_souls + ?,
                     e_crystals = e_crystals + ?,
                     armor_parts = armor_parts + ?
                 WHERE user_id = ?''', 
                 (new_hp, xp_change, money_change, parts_change, user_id))
    conn.commit()
    conn.close()
    return new_hp

def update_stats(user_id, level, max_hp):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE hunters SET level = ?, max_hp = ? WHERE user_id = ?", (level, max_hp, user_id))
    conn.commit()
    conn.close()

def modify_hp(user_id, amount):
    return update_hunter_stats(user_id, hp_change=amount)

# --- EQUIPO Y CRAFTEO ---

def get_total_defense(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(defense) FROM equipment WHERE user_id = ?", (user_id,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0

def damage_equipment(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE equipment SET current_durability = current_durability - 1 WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM equipment WHERE current_durability <= 0 AND user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def perform_crafting(user_id, parts_cost, money_cost):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT e_crystals, armor_parts FROM hunters WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result: return "NO_DATA"
    if result[0] < money_cost: return "NO_MONEY"
    if result[1] < parts_cost: return "NO_PARTS"
    
    c.execute('''UPDATE hunters 
                 SET e_crystals = e_crystals - ?, 
                     armor_parts = armor_parts - ? 
                 WHERE user_id = ?''', (money_cost, parts_cost, user_id))
    conn.commit()
    conn.close()
    return "OK"

def equip_armor(user_id, slot, item_name, defense, durability):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""REPLACE INTO equipment (user_id, slot, item_name, defense, current_durability, max_durability)
                 VALUES (?, ?, ?, ?, ?, ?)""", 
                 (user_id, slot, item_name, defense, durability, durability))
    conn.commit()
    conn.close()

# --- TIENDA, ITEMS Y BUFFS (NUEVO) ---

def purchase_item(user_id, cost, item_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT e_crystals FROM hunters WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    
    if not result or result[0] < cost:
        conn.close()
        return False 
    
    c.execute("UPDATE hunters SET e_crystals = e_crystals - ? WHERE user_id = ?", (cost, user_id))
    c.execute("""INSERT INTO inventory (user_id, item_name, quantity) 
                 VALUES (?, ?, 1) 
                 ON CONFLICT(user_id, item_name) 
                 DO UPDATE SET quantity = quantity + 1""", (user_id, item_name))
    conn.commit()
    conn.close()
    return True

def get_inventory(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT item_name, quantity FROM inventory WHERE user_id = ?", (user_id,))
    items = c.fetchall()
    conn.close()
    return items

def consume_item(user_id, item_name):
    """Resta 1 al item. Si llega a 0, lo borra. Devuelve True si se pudo."""
    conn = get_connection()
    c = conn.cursor()
    
    # Verificar cantidad
    c.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, item_name))
    res = c.fetchone()
    
    if not res or res[0] < 1:
        conn.close()
        return False # No tiene el item
    
    # Restar
    if res[0] > 1:
        c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE user_id = ? AND item_name = ?", (user_id, item_name))
    else:
        c.execute("DELETE FROM inventory WHERE user_id = ? AND item_name = ?", (user_id, item_name))
        
    conn.commit()
    conn.close()
    return True

def activate_buff(user_id, buff_type, multiplier, duration_seconds):
    """Activa un chip (Buff)"""
    conn = get_connection()
    c = conn.cursor()
    end_time = time.time() + duration_seconds
    c.execute("""REPLACE INTO active_buffs (user_id, buff_type, multiplier, end_time)
                 VALUES (?, ?, ?, ?)""", (user_id, buff_type, multiplier, end_time))
    conn.commit()
    conn.close()

def get_active_buffs(user_id):
    """Obtiene buffs activos y limpia los expirados"""
    conn = get_connection()
    c = conn.cursor()
    now = time.time()
    
    # Borrar expirados
    c.execute("DELETE FROM active_buffs WHERE user_id = ? AND end_time < ?", (user_id, now))
    conn.commit()
    
    # Obtener vigentes
    c.execute("SELECT buff_type, multiplier, end_time FROM active_buffs WHERE user_id = ?", (user_id,))
    buffs = c.fetchall()
    conn.close()
    return buffs # Lista de (type, mult, end_time)

# --- JEFE ---
def spawn_boss(name, hp, image_url):
    conn = get_connection()
    c = conn.cursor()
    c.execute("REPLACE INTO active_boss (id, name, max_hp, current_hp, image_url, active) VALUES (1, ?, ?, ?, ?, 1)", 
              (name, hp, hp, image_url))
    conn.commit()
    conn.close()

def get_boss():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, max_hp, current_hp, image_url, active FROM active_boss WHERE id = 1 AND active = 1")
    data = c.fetchone()
    conn.close()
    return data 

def damage_boss(amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE active_boss SET current_hp = current_hp - ? WHERE id = 1", (amount,))
    c.execute("SELECT current_hp FROM active_boss WHERE id = 1")
    hp = c.fetchone()[0]
    if hp <= 0:
        c.execute("UPDATE active_boss SET active = 0 WHERE id = 1")
    conn.commit()
    conn.close()
    return hp