import pygame, random, math, sys
pygame.init()

info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("BHAVNOBI")
clock = pygame.time.Clock()
FPS = 60

font_title = pygame.font.SysFont("Courier New", 72, bold=True)
font_big   = pygame.font.SysFont("Courier New", 36, bold=True)
font_med   = pygame.font.SysFont("Courier New", 22, bold=True)
font_small = pygame.font.SysFont("Courier New", 15)
font_tiny  = pygame.font.SysFont("Courier New", 12)

THEMES = [
    ((4,4,14),  (8,8,22),  (25,80,50), (12,50,32), (93,202,165),(12,22,40)),
    ((4,10,4),  (8,20,8),  (22,55,100),(10,32,60), (133,183,235),(10,30,20)),
    ((14,5,4),  (22,8,8),  (80,50,22), (55,32,10), (239,159,39), (30,15,10)),
]
theme_idx = 0

# ── Biomes — shift every 1500px of world distance ────────────────────────────
# Each biome: (name, bg_top, bg_bot, plat_top, plat_shd, accent, mtn_col,
#              particle_col, particle_type, gravity_mult)
BIOMES = [
    {"name":"Forest",  "icon":"🌲",
     "bg_top":(4,12,4),   "bg_bot":(6,20,6),
     "plat_top":(25,80,30),"plat_shd":(12,55,18),
     "accent":(80,200,80), "mtn_col":(10,30,12),
     "ptcl":(60,180,40),  "ptcl_type":"leaf",
     "grav":1.0},
    {"name":"Cave",    "icon":"🪨",
     "bg_top":(8,6,14),   "bg_bot":(12,10,20),
     "plat_top":(50,40,80),"plat_shd":(30,22,55),
     "accent":(160,80,255),"mtn_col":(20,15,35),
     "ptcl":(180,100,255),"ptcl_type":"drip",
     "grav":1.0},
    {"name":"Volcano", "icon":"🌋",
     "bg_top":(20,5,2),   "bg_bot":(35,10,4),
     "plat_top":(90,40,10),"plat_shd":(60,20,5),
     "accent":(255,120,20),"mtn_col":(40,15,5),
     "ptcl":(255,80,20),  "ptcl_type":"ember",
     "grav":1.0},
    {"name":"Space",   "icon":"🌌",
     "bg_top":(2,2,10),   "bg_bot":(4,4,18),
     "plat_top":(30,30,60),"plat_shd":(15,15,40),
     "accent":(80,200,255),"mtn_col":(8,8,25),
     "ptcl":(200,220,255),"ptcl_type":"star",
     "grav":0.55},   # lower gravity in space!
]
BIOME_LEN = 1500   # world-x distance per biome

def get_biome(cam_x):
    idx=int(max(0,cam_x)//BIOME_LEN)%len(BIOMES)
    return BIOMES[idx]

def get_biome_at(world_x):
    idx=int(max(0,world_x)//BIOME_LEN)%len(BIOMES)
    return BIOMES[idx]

# ── Placeable blocks — coin-economy build system ──────────────────────────────
# cost=gold to place, refund=gold back when broken
BLOCK_TYPES = {
    "stone": {"name":"Stone",  "cost":1,"refund":1,"color":(100,100,110),"col2":(70,70,80),
              "hp":3, "desc":"Solid wall. 1g place/break"},
    "spike": {"name":"Spike",  "cost":5,"refund":2,"color":(180,60,60),  "col2":(120,30,30),
              "hp":2, "dmg":3, "desc":"Damages enemies. 5g place"},
    "bounce":{"name":"Bounce", "cost":3,"refund":2,"color":(60,200,120), "col2":(30,140,70),
              "hp":2, "bounce":True, "desc":"Bounces player/enemies. 3g"},
}

GRAVITY=0.28; GRAVITY_FALL=0.55; SPEED=3.6; JUMP_V=-11.5
DEATH_Y = HEIGHT*0.75 + HEIGHT*0.4
MAX_HP = 10  # Raised so armor def (1-5) is meaningful

# How much damage each enemy type deals per hit (before armor reduction)
ENEMY_DMG = {"walker":2,"archer":2,"jumper":3,"bomber":4,"knight":3,
             "ghost":2,"troll":4,"dark_archer":3,"slime":1,"ninja_e":2}

# ─────────────────────────────────────────────────────────────────────────────
# ITEM DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
# category: weapon | armor | food | potion
# source: ground | trader | trial | drop
ITEMS = {
    # ===== WEAPONS =====
    "wood_sword":   {"name":"Wood Sword |T1",   "cat":"weapon","dmg":1,"color":(139,100,20), "price":0,  "source":["ground"],         "desc":"Basic wooden blade. T1"},
    "bone_club":    {"name":"Bone Club |T1",    "cat":"weapon","dmg":1,"color":(200,190,160),"price":5,  "source":["drop"],           "desc":"Crude bone club. T1"},
    "iron_sword":   {"name":"Iron Sword |T2",   "cat":"weapon","dmg":2,"color":(180,180,180),"price":30, "source":["trader","drop"],  "desc":"Sharp iron blade. T2"},
    "steel_blade":  {"name":"Steel Blade |T2",  "cat":"weapon","dmg":2,"color":(200,200,210),"price":35, "source":["trader"],         "desc":"Refined steel. T2"},
    "bronze_axe":   {"name":"Bronze Axe |T2",   "cat":"weapon","dmg":2,"color":(210,140,60), "price":32, "source":["trader","drop"],  "desc":"Bronze splitting axe. T2"},
    "gold_sword":   {"name":"Gold Sword |T3",   "cat":"weapon","dmg":3,"color":(255,200,0),  "price":80, "source":["trader","trial"], "desc":"Gleaming gold blade. T3"},
    "diamond_edge": {"name":"Diamond Edge |T3", "cat":"weapon","dmg":3,"color":(100,200,255),"price":90, "source":["trial"],          "desc":"Crystal sharp. T3"},
    "flame_blade":  {"name":"Flame Blade |T3",  "cat":"weapon","dmg":3,"color":(255,100,20), "price":85, "source":["trader","trial"], "desc":"Engulfed in flames. T3"},
    "ice_shard":    {"name":"Ice Shard |T3",    "cat":"weapon","dmg":3,"color":(150,220,255),"price":82, "source":["trial"],          "desc":"Frozen crystal blade. T3"},
    "shadow_blade": {"name":"Shadow Blade |T4", "cat":"weapon","dmg":4,"color":(100,0,200),  "price":120,"source":["trial","drop"],   "desc":"Wreathed in darkness. T4"},
    "obsidian_edge":{"name":"Obsidian Edge |T4","cat":"weapon","dmg":4,"color":(50,50,80),   "price":115,"source":["trial"],          "desc":"Volcanic obsidian. T4"},
    "void_cleaver": {"name":"Void Cleaver |T5", "cat":"weapon","dmg":5,"color":(80,0,120),   "price":180,"source":["trial"],          "desc":"Cuts through dimensions. T5"},
    "excalibur":    {"name":"Excalibur |T5",    "cat":"weapon","dmg":5,"color":(200,220,255),"price":200,"source":["trial"],          "desc":"Legendary power. T5"},
    "dragon_fang":  {"name":"Dragon Fang |T6",  "cat":"weapon","dmg":6,"color":(220,100,0),  "price":250,"source":["trial"],          "desc":"Ancient dragon fang. T6"},
    "cosmic_blade": {"name":"Cosmic Blade |T7", "cat":"weapon","dmg":7,"color":(150,50,255), "price":300,"source":["trial"],          "desc":"Forged from stardust. T7"},
    # ===== ARMOR =====
    "cloth":        {"name":"Cloth Armor |T0",  "cat":"armor","def":0,  "color":(180,160,140),"price":0,  "source":["ground"],         "desc":"Basic cloth wrap. T0"},
    "leather":      {"name":"Leather Armor |T1","cat":"armor","def":1,  "color":(160,100,50), "price":25, "source":["trader","drop"],  "desc":"Tough leather. T1"},
    "leather_plus": {"name":"Leather+  |T1",     "cat":"armor","def":1,  "color":(180,120,60), "price":30, "source":["trader"],         "desc":"Reinforced leather. T1"},
    "ring_mail":    {"name":"Ring Mail |T2",    "cat":"armor","def":2,  "color":(170,170,170),"price":28, "source":["trader","drop"],  "desc":"Interlocked rings. T1"},
    "chainmail":    {"name":"Chainmail |T2",    "cat":"armor","def":2,  "color":(160,160,200),"price":60, "source":["trader","trial"], "desc":"Linked chain. T2"},
    "mithril_mail": {"name":"Mithril Mail |T2", "cat":"armor","def":2,  "color":(120,180,200),"price":70, "source":["trial"],          "desc":"Mythical metal. T2"},
    "scale_mail":   {"name":"Scale Mail |T2",   "cat":"armor","def":2,  "color":(140,160,100),"price":65, "source":["trader"],         "desc":"Overlapping scales. T2"},
    "plate":        {"name":"Plate Armor |T3",  "cat":"armor","def":3,  "color":(200,200,220),"price":120,"source":["trial","drop"],   "desc":"Heavy plating. T3"},
    "bronze_plate": {"name":"Bronze Plate |T3", "cat":"armor","def":3,  "color":(210,140,60), "price":115,"source":["trial"],          "desc":"Bronze reinforced. T3"},
    "adamant":      {"name":"Adamant |T4",      "cat":"armor","def":4,  "color":(80,120,180), "price":180,"source":["trial"],          "desc":"Nearly unbreakable. T4"},
    "crystal_mail": {"name":"Crystal Mail |T4", "cat":"armor","def":4,  "color":(150,200,255),"price":185,"source":["trial"],          "desc":"Crystalline plates. T4"},
    "void_armor":   {"name":"Void Armor |T5",   "cat":"armor","def":5,  "color":(100,50,150), "price":250,"source":["trial"],          "desc":"Abyssal protection. T5"},
    "dragon_scale": {"name":"Dragon Scale |T5", "cat":"armor","def":5,  "color":(180,100,50), "price":260,"source":["trial"],          "desc":"Impenetrable scales. T5"},
    # ===== GOLD =====
    "gold_coin":    {"name":"Gold Coin",    "cat":"gold","gold":5,  "color":(255,200,30),"price":0,"source":["ground"],"desc":"+5 gold."},
    "gold_pile":    {"name":"Gold Pile",    "cat":"gold","gold":15, "color":(255,180,0), "price":0,"source":["ground"],"desc":"+15 gold."},
    "gold_chest":   {"name":"Gold Chest",   "cat":"gold","gold":40, "color":(255,160,0), "price":0,"source":["ground"],"desc":"+40 gold."},
    # ===== FOOD - BASIC HEALING (ground spawnable) =====
    "apple":        {"name":"Apple",        "cat":"food","hp":2, "effect":None,    "dur":0,  "color":(220,50,50),  "price":3, "source":["ground"],         "desc":"Heals 2 HP."},
    "berry":        {"name":"Berry",        "cat":"food","hp":2, "effect":None,    "dur":0,  "color":(160,0,220),  "price":2, "source":["ground"],         "desc":"Heals 2 HP."},
    "orange":       {"name":"Orange",       "cat":"food","hp":2, "effect":None,    "dur":0,  "color":(255,140,0),  "price":3, "source":["ground"],         "desc":"Citrus heal 2."},
    "pear":         {"name":"Pear",         "cat":"food","hp":2, "effect":None,    "dur":0,  "color":(200,180,80), "price":3, "source":["ground"],         "desc":"Heals 2 HP."},
    "mushroom":     {"name":"Mushroom",     "cat":"food","hp":0, "effect":"regen", "dur":300,"color":(180,140,100),"price":8, "source":["ground"],         "desc":"Regen 5s."},
    # ===== FOOD - TRADER =====
    "bread":        {"name":"Bread",        "cat":"food","hp":3, "effect":None,    "dur":0,  "color":(210,170,80), "price":10,"source":["trader"],         "desc":"Heals 3 HP."},
    "meat":         {"name":"Meat",         "cat":"food","hp":3, "effect":None,    "dur":0,  "color":(180,50,50),  "price":12,"source":["trader"],         "desc":"Heals 3 HP."},
    "steak":        {"name":"Steak",        "cat":"food","hp":5, "effect":None,    "dur":0,  "color":(150,40,30),  "price":20,"source":["trader"],         "desc":"Heals 5 HP."},
    "roasted_fish": {"name":"Roasted Fish", "cat":"food","hp":4, "effect":None,    "dur":0,  "color":(220,140,80), "price":14,"source":["trader"],         "desc":"Heals 4 HP."},
    "magic_shroom": {"name":"Magic Shroom", "cat":"food","hp":2, "effect":"regen", "dur":400,"color":(200,150,255),"price":15,"source":["trader"],         "desc":"Heal+regen."},
    "honey_cake":   {"name":"Honey Cake",   "cat":"food","hp":3, "effect":"regen", "dur":300,"color":(255,220,100),"price":18,"source":["trader"],         "desc":"Heal+regen."},
    "spicy_rice":   {"name":"Spicy Rice",   "cat":"food","hp":2, "effect":"speed", "dur":420,"color":(255,140,0),  "price":15,"source":["trader"],         "desc":"Heal+speed 7s."},
    "pepper_stew":  {"name":"Pepper Stew",  "cat":"food","hp":2, "effect":"power", "dur":360,"color":(200,80,40),  "price":17,"source":["trader"],         "desc":"Heal+power 6s."},
    "dragon_fruit": {"name":"Dragon Fruit", "cat":"food","hp":2, "effect":"power", "dur":300,"color":(255,80,150), "price":25,"source":["trader"],         "desc":"Heal+power 5s."},
    "energy_bar":   {"name":"Energy Bar",   "cat":"food","hp":2, "effect":"speed", "dur":300,"color":(200,200,80),  "price":14,"source":["trader"],         "desc":"Heal+speed."},
    "golden_apple": {"name":"Golden Apple", "cat":"food","hp":6, "effect":"regen", "dur":600,"color":(255,220,0),   "price":50,"source":["trader","trial"], "desc":"Big heal+regen 10s."},
    "divine_fruit": {"name":"Divine Fruit", "cat":"food","hp":4, "effect":"barrier","dur":600,"color":(200,150,255),"price":45,"source":["trial"],          "desc":"Heal+shield 10s."},
    # ===== POTIONS =====
    "health_pot":   {"name":"Health Pot",   "cat":"potion","hp":3, "effect":None,    "dur":0,  "color":(220,50,50),  "price":18,"source":["trader"],         "desc":"Heal 3 HP."},
    "mega_heal":    {"name":"Mega Heal",    "cat":"potion","hp":6, "effect":None,    "dur":0,  "color":(255,80,80),  "price":35,"source":["trader","trial"], "desc":"Heal 6 HP."},
    "speed_pot":    {"name":"Speed Pot",    "cat":"potion","hp":0, "effect":"speed", "dur":500,"color":(80,200,255), "price":22,"source":["trader"],         "desc":"Speed 8s."},
    "haste_pot":    {"name":"Haste Pot",    "cat":"potion","hp":0, "effect":"speed", "dur":600,"color":(100,220,255),"price":28,"source":["trader","trial"], "desc":"Speed 10s."},
    "shield_pot":   {"name":"Shield Pot",   "cat":"potion","hp":0, "effect":"barrier","dur":600,"color":(100,160,255),"price":30,"source":["trader"],        "desc":"Shield 10s."},
    "guardian_pot": {"name":"Guardian Pot", "cat":"potion","hp":2, "effect":"barrier","dur":750,"color":(120,180,255),"price":40,"source":["trial"],         "desc":"Heal+shield 12s."},
    "rage_pot":     {"name":"Rage Pot",     "cat":"potion","hp":0, "effect":"power", "dur":360,"color":(255,80,0),   "price":40,"source":["trader","trial"], "desc":"+2 dmg 6s."},
    "berserk_pot":  {"name":"Berserk Pot",  "cat":"potion","hp":0, "effect":"power", "dur":480,"power_bonus":3,"color":(255,50,0),"price":50,"source":["trial"],"desc":"+3 dmg 8s."},
    "invis_pot":    {"name":"Invis Pot",    "cat":"potion","hp":0, "effect":"invis", "dur":300,"color":(200,200,255),"price":45,"source":["trader","trial"], "desc":"Invisible 5s."},
    "shadow_pot":   {"name":"Shadow Pot",   "cat":"potion","hp":0, "effect":"invis", "dur":420,"color":(150,100,200),"price":55,"source":["trial"],          "desc":"Invis 7s."},
}

WEAPON_SLOTS = ["wood_sword","bone_club","iron_sword","steel_blade","bronze_axe",
                "gold_sword","diamond_edge","flame_blade","ice_shard",
                "shadow_blade","obsidian_edge","void_cleaver","excalibur",
                "dragon_fang","cosmic_blade"]
ARMOR_SLOTS  = ["cloth","leather","leather_plus","ring_mail","chainmail","mithril_mail",
                "scale_mail","plate","bronze_plate","adamant","crystal_mail",
                "void_armor","dragon_scale"]

# ─────────────────────────────────────────────────────────────────────────────
# RELIC DEFINITIONS  (passive effects, max 3 equipped at once)
# ─────────────────────────────────────────────────────────────────────────────
RELICS = {
    # ── Combat ───────────────────────────────────────────────────────────────
    "bloodstone":     {"name":"Bloodstone",     "color":(220,60,60),  "gem":(180,30,30),
                       "desc":"Kill = heal 1 HP","passive":"lifesteal"},
    "berserker_tooth":{"name":"Berserker Tooth", "color":(255,120,0),  "gem":(200,80,0),
                       "desc":"+1 dmg per 3 combo","passive":"combo_dmg"},
    "phantom_edge":   {"name":"Phantom Edge",    "color":(180,100,255),"gem":(120,50,200),
                       "desc":"Every 5th slash = 3x dmg","passive":"phantom"},
    "quiver":         {"name":"Shuriken Quiver", "color":(80,200,180), "gem":(40,150,130),
                       "desc":"Max ammo x2, fast regen","passive":"quiver"},
    "stomp_boots":    {"name":"Stomp Boots",     "color":(200,140,60), "gem":(150,90,20),
                       "desc":"Stomps bounce higher+AoE","passive":"stomp"},
    # ── Defense ──────────────────────────────────────────────────────────────
    "iron_will":      {"name":"Iron Will",       "color":(160,160,200),"gem":(100,100,160),
                       "desc":"-1 all damage taken","passive":"iron_will"},
    "last_stand":     {"name":"Last Stand",      "color":(255,50,50),  "gem":(200,20,20),
                       "desc":"<3 HP: +2 DEF + glow","passive":"last_stand"},
    "medic_bag":      {"name":"Medic's Bag",     "color":(80,200,100), "gem":(40,150,60),
                       "desc":"Regen lasts 2x longer","passive":"medic"},
    "shield_rune":    {"name":"Shield Rune",     "color":(100,160,255),"gem":(50,100,220),
                       "desc":"Shield cooldown halved","passive":"shield_rune"},
    # ── Utility ──────────────────────────────────────────────────────────────
    "dash_stone":     {"name":"Dash Stone",      "color":(80,220,255), "gem":(30,160,220),
                       "desc":"Dash CD halved, fire trail","passive":"dash_stone"},
    "gravity_gem":    {"name":"Gravity Gem",     "color":(150,200,255),"gem":(80,140,220),
                       "desc":"Hold jump to float","passive":"gravity"},
    "gold_magnet":    {"name":"Gold Magnet",     "color":(255,220,30), "gem":(200,160,0),
                       "desc":"Auto-collect gold 100px","passive":"magnet"},
    "merchant_eye":   {"name":"Merchant's Eye",  "color":(200,160,255),"gem":(140,80,200),
                       "desc":"+2 trader stock, -20% price","passive":"merchant"},
    # ── Legendary ────────────────────────────────────────────────────────────
    "soul_lantern":   {"name":"Soul Lantern",    "color":(255,255,150),"gem":(220,200,50),
                       "desc":"Revive once with 5 HP","passive":"revive"},
    "dragon_heart":   {"name":"Dragon Heart",    "color":(220,80,30),  "gem":(180,40,0),
                       "desc":"Max HP +5","passive":"dragon_heart"},
    "void_step":      {"name":"Void Step",       "color":(100,50,200), "gem":(60,20,160),
                       "desc":"Dashing through enemy damages","passive":"void_step"},
    "warlord_crown":  {"name":"Warlord's Crown", "color":(255,200,0),  "gem":(200,140,0),
                       "desc":"Combo never resets on hit","passive":"warlord"},
}

def alpha_rect(surf,color,rect,alpha):
    s=pygame.Surface((max(1,int(rect[2])),max(1,int(rect[3]))),pygame.SRCALPHA)
    s.fill((*color[:3],int(max(0,min(255,alpha)))))
    surf.blit(s,(int(rect[0]),int(rect[1])))

# ─────────────────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self,x,y,color,spd=3,life=1.0,size=None):
        self.x=x+random.uniform(-2,2); self.y=y+random.uniform(-2,2)
        a=random.uniform(0,math.pi*2); s=random.uniform(0.3,spd)
        self.vx=math.cos(a)*s; self.vy=math.sin(a)*s-1
        self.life=life; self.max_life=life; self.color=color
        self.size=size or random.uniform(2,5)
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=0.12; self.vx*=0.98
        self.life-=0.03; return self.life>0
    def draw(self,surf,cx,cy):
        t=self.life/self.max_life; alpha=max(0,min(255,int(t*230)))
        size=max(1,int(self.size*t))
        px=int(self.x-cx); py=int(self.y-cy)
        if -10<px<WIDTH+10 and -10<py<HEIGHT+10:
            s=pygame.Surface((size*2,size*2),pygame.SRCALPHA)
            pygame.draw.rect(s,(*self.color[:3],alpha),(0,0,size*2,size*2))
            surf.blit(s,(px-size,py-size))

class Ghost:
    def __init__(self,x,y,w,h,color): self.x=x;self.y=y;self.w=w;self.h=h;self.color=color;self.life=0.6
    def update(self): self.life-=0.08; return self.life>0
    def draw(self,surf,cx,cy): alpha_rect(surf,self.color,(int(self.x-cx),int(self.y-cy),self.w,self.h),max(0,int(self.life/0.6*70)))

class DmgNum:
    def __init__(self,x,y,text,color,big=False):
        self.x=x;self.y=y;self.vy=-2.2;self.life=1.0
        self.text=str(text);self.color=color;self.font=font_med if big else font_small
    def update(self): self.y+=self.vy;self.vy*=0.93;self.life-=0.02;return self.life>0
    def draw(self,surf,cx,cy):
        img=self.font.render(self.text,True,self.color); img.set_alpha(max(0,min(255,int(self.life*255))))
        surf.blit(img,(int(self.x-cx)-img.get_width()//2,int(self.y-cy)))

# ─────────────────────────────────────────────────────────────────────────────
# Ground Item (pickupable)
# ─────────────────────────────────────────────────────────────────────────────
class GroundItem:
    def __init__(self,x,y,item_key):
        self.x=x; self.y=y; self.w=16; self.h=16
        self.key=item_key; self.bob=random.uniform(0,math.pi*2)
        self.vx=random.uniform(-1,1); self.vy=-3; self.on_ground=False
    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self,platforms):
        if not self.on_ground:
            self.vy+=0.3; self.x+=self.vx; self.y+=self.vy
            self.vx*=0.95
            for p in platforms:
                if pygame.Rect(self.x,self.y,self.w,self.h).colliderect(p.rect()):
                    if self.vy>0: self.y=p.y-self.h; self.vy=0; self.vx*=0.5; self.on_ground=True
        self.bob+=0.05
    def draw(self,surf,cx,cy):
        rx=int(self.x-cx); ry=int(self.y-cy)-int(math.sin(self.bob)*3)
        data=ITEMS.get(self.key,{})
        col=data.get("color",(200,200,200))
        cat=data.get("cat","")

        if cat=="gold":
            # Gold coin — circle with $ symbol feel
            amt=data.get("gold",5)
            size=6 if amt<=5 else 9 if amt<=15 else 13
            pygame.draw.circle(surf,col,(rx+self.w//2,ry+self.h//2),size)
            pygame.draw.circle(surf,(255,255,255),(rx+self.w//2,ry+self.h//2),size,1)
            if amt>=15:
                # Pile — draw multiple coins stacked
                pygame.draw.circle(surf,col,(rx+self.w//2-4,ry+self.h//2+3),6)
                pygame.draw.circle(surf,col,(rx+self.w//2+4,ry+self.h//2+3),6)
            # Gold glow pulse
            alpha_rect(surf,col,(rx+self.w//2-size-3,ry+self.h//2-size-3,(size+3)*2,(size+3)*2),
                       int(30+20*math.sin(self.bob*2)))
            # Amount label
            lbl=font_tiny.render(f"+{amt}g",True,col)
            surf.blit(lbl,(rx+self.w//2-lbl.get_width()//2,ry-10))
            return

        pygame.draw.rect(surf,col,(rx,ry,self.w,self.h))
        pygame.draw.rect(surf,(255,255,255),(rx,ry,self.w,self.h),1)
        # Category icon
        if cat=="food" or cat=="potion":
            pygame.draw.circle(surf,(255,255,255),(rx+8,ry+8),4)
        elif cat=="weapon":
            pygame.draw.line(surf,(255,255,255),(rx+3,ry+13),(rx+13,ry+3),2)
        elif cat=="armor":
            pygame.draw.polygon(surf,(255,255,255),[(rx+8,ry+2),(rx+14,ry+6),(rx+14,ry+12),(rx+8,ry+14),(rx+2,ry+12),(rx+2,ry+6)])
        # Glow
        alpha_rect(surf,col,(rx-2,ry-2,self.w+4,self.h+4),int(40+20*math.sin(self.bob)))

# ─────────────────────────────────────────────────────────────────────────────
# Platform
# ─────────────────────────────────────────────────────────────────────────────
class Platform:
    def __init__(self,x,y,w,ptype="solid"):
        self.x=x;self.y=y;self.w=w;self.h=14;self.type=ptype
        self.orig_x=x;self.range=random.uniform(50,100)
        self.spd=random.uniform(0.7,1.4);self.dir=1;self.tick=0
    def update(self):
        if self.type=="moving":
            self.x+=self.spd*self.dir
            if abs(self.x-self.orig_x)>self.range: self.dir*=-1
        self.tick+=1
    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def draw(self,surf,cx,cy,accent,pt,ps):
        rx=int(self.x-cx);ry=int(self.y-cy)
        if rx+self.w<-20 or rx>WIDTH+20 or ry<-20 or ry>HEIGHT+20: return
        pygame.draw.rect(surf,pt,(rx,ry,self.w,self.h))
        pygame.draw.rect(surf,ps,(rx,ry,self.w,5))
        pygame.draw.rect(surf,ps,(rx,ry+self.h-3,self.w,3))
        alpha_rect(surf,accent,(rx,ry,self.w,2),int(55+35*math.sin(self.tick*0.04)))
        if self.type=="drop":
            for dx in range(0,int(self.w),10):
                if (dx//10+self.tick//6)%2==0:
                    pygame.draw.line(surf,(*accent,180),(rx+dx,ry),(rx+min(dx+5,int(self.w)),ry),2)
            pygame.draw.rect(surf,(*accent,55),(rx,ry,self.w,self.h),1)
        if self.type=="moving":
            p2=int(100+80*math.sin(pygame.time.get_ticks()*0.006))
            alpha_rect(surf,accent,(rx,ry,self.w,3),p2)

# ─────────────────────────────────────────────────────────────────────────────
# Shuriken / Bomb
# ─────────────────────────────────────────────────────────────────────────────
class Shuriken:
    def __init__(self,x,y,vx,vy,from_enemy=False):
        self.x=x;self.y=y;self.vx=vx;self.vy=vy
        self.w=12;self.h=12;self.rot=0.0;self.life=220;self.bounces=0;self.from_enemy=from_enemy
    def update(self):
        self.x+=self.vx;self.y+=self.vy;self.vy+=0.12;self.rot+=0.45;self.life-=1
        # Homing behaviour for dark archer arrows
        if getattr(self,'homing',False) and self.homing_target:
            target=self.homing_target[0]
            dx=target.x+target.w/2-self.x; dy=target.y+target.h/2-self.y
            dist=max(1,math.hypot(dx,dy))
            self.vx+=(dx/dist*0.4); self.vy+=(dy/dist*0.3)
            # Cap speed
            spd=math.hypot(self.vx,self.vy)
            if spd>9: self.vx=self.vx/spd*9; self.vy=self.vy/spd*9
        return self.life>0
    def rect(self): return pygame.Rect(self.x-6,self.y-6,self.w,self.h)
    def draw(self,surf,cx,cy,color):
        px=int(self.x-cx);py=int(self.y-cy)
        if px<-20 or px>WIDTH+20: return
        for i in range(4):
            a=self.rot+i*math.pi/2
            tip=(px+math.cos(a)*6,py+math.sin(a)*6)
            side=(px+math.cos(a+1.6)*2.4,py+math.sin(a+1.6)*2.4)
            back=(px+math.cos(a+math.pi)*2.1,py+math.sin(a+math.pi)*2.1)
            pygame.draw.polygon(surf,color,[tip,side,back])
        pygame.draw.circle(surf,(230,230,230),(px,py),2)
        alpha_rect(surf,color,(px-6,py-6,12,12),22)

class Bomb:
    def __init__(self,x,y,vx,vy): self.x=x;self.y=y;self.vx=vx;self.vy=vy;self.w=10;self.h=10;self.life=180;self.bounces=0;self.fuse=70
    def update(self): self.x+=self.vx;self.y+=self.vy;self.vy+=0.25;self.vx*=0.99;self.life-=1;self.fuse-=1;return self.life>0 and self.fuse>-1
    def rect(self): return pygame.Rect(self.x-5,self.y-5,self.w,self.h)
    def draw(self,surf,cx,cy):
        px=int(self.x-cx);py=int(self.y-cy)
        if px<-20 or px>WIDTH+20: return
        pygame.draw.circle(surf,(30,30,30),(px,py),6)
        pygame.draw.circle(surf,(60,60,60),(px-1,py-1),3)
        if self.fuse>0:
            pulse=int(200+55*math.sin(self.life*0.3))
            pygame.draw.circle(surf,(pulse,pulse//2,0),(px+4,py-6),3)
            alpha_rect(surf,(255,150,0),(px+2,py-8,6,6),pulse//2)

# ─────────────────────────────────────────────────────────────────────────────
# Placed Block — player-built structures
# ─────────────────────────────────────────────────────────────────────────────
BLOCK_SIZE = 28   # pixels per block

class PlacedBlock:
    def __init__(self, gx, gy, btype):
        # gx/gy are grid coordinates, world pos = gx*BLOCK_SIZE, gy*BLOCK_SIZE
        self.gx=gx; self.gy=gy
        self.x=gx*BLOCK_SIZE; self.y=gy*BLOCK_SIZE
        self.w=BLOCK_SIZE; self.h=BLOCK_SIZE
        self.btype=btype
        d=BLOCK_TYPES[btype]
        self.hp=d["hp"]; self.max_hp=d["hp"]
        self.hit_flash=0

    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)

    def draw(self,surf,cx,cy):
        rx=int(self.x-cx); ry=int(self.y-cy)
        if rx+self.w<-10 or rx>WIDTH+10 or ry+self.h<-10 or ry>HEIGHT+10: return
        d=BLOCK_TYPES[self.btype]
        col=d["color"]; col2=d["col2"]
        # Flash white when hit
        if self.hit_flash>0:
            self.hit_flash-=1
            col=(220,220,220); col2=(180,180,180)
        pygame.draw.rect(surf,col,(rx,ry,self.w,self.h))
        pygame.draw.rect(surf,col2,(rx,ry,self.w,4))       # top shadow
        pygame.draw.rect(surf,col2,(rx,ry+self.h-4,self.w,4))  # bottom shadow
        pygame.draw.rect(surf,(30,25,35),(rx,ry,self.w,self.h),1)  # outline
        # HP crack overlay
        if self.hp<self.max_hp:
            crack_alpha=int(80*(1-self.hp/self.max_hp))
            alpha_rect(surf,(0,0,0),(rx,ry,self.w,self.h),crack_alpha)
        # Type-specific visuals
        if self.btype=="spike":
            for sx2 in range(4,self.w-2,6):
                pygame.draw.polygon(surf,(220,80,80),
                    [(rx+sx2,ry+4),(rx+sx2+3,ry+self.h-4),(rx+sx2-3,ry+self.h-4)])
        elif self.btype=="bounce":
            # Spring coil lines
            for ly in range(6,self.h-4,5):
                pygame.draw.line(surf,(100,255,160),(rx+4,ry+ly),(rx+self.w-4,ry+ly),1)
            pygame.draw.rect(surf,(80,230,140),(rx+4,ry+self.h-6,self.w-8,4))
        elif self.btype=="stone":
            # Brick pattern
            for bry in range(0,self.h,9):
                off=7 if (bry//9)%2==0 else 0
                for brx in range(-off,self.w,14):
                    pygame.draw.rect(surf,col2,(rx+brx,ry+bry,12,7),1)

class SlashFX:
    def __init__(self,x,y,w,h,direction,accent,color=None):
        self.x=x;self.y=y;self.w=w;self.h=h;self.direction=direction
        self.life=14;self.max_life=14;self.accent=color or accent
    def update(self): self.life-=1;return self.life>0
    def draw(self,surf,cx,cy):
        prog=1-self.life/self.max_life;alpha=int((1-prog)*220)
        acx=int(self.x+self.w/2-cx);acy=int(self.y+self.h/2-cy)
        radius=int(self.w*1.1);r,g,b=self.accent
        arc=pygame.Surface((radius*2+14,radius*2+14),pygame.SRCALPHA)
        offset=prog*0.6*self.direction;pts=[]
        for i in range(25):
            a=-math.pi/2.5+(math.pi/1.25)*i/24+offset
            pts.append((radius+7+math.cos(a)*radius,radius+7+math.sin(a)*radius))
        if len(pts)>1:
            pygame.draw.lines(arc,(r,g,b,alpha),False,pts,4)
            pygame.draw.lines(arc,(r,g,b,alpha//3),False,pts,9)
        surf.blit(arc,(acx-radius-7,acy-radius-7))
        alpha_rect(surf,(r,g,b),(int(self.x-cx),int(self.y-cy),self.w,self.h),int((1-prog)*40))

# ─────────────────────────────────────────────────────────────────────────────
# Trader NPC
# ─────────────────────────────────────────────────────────────────────────────
class Trader:
    def __init__(self,x,y,plat):
        self.x=x;self.y=y;self.w=20;self.h=30;self.plat=plat
        self.bob=random.uniform(0,math.pi*2)
        # Build stock: random selection of trader-source items
        all_trader=[(k,v) for k,v in ITEMS.items() if "trader" in v["source"]]
        random.shuffle(all_trader)
        self.stock=all_trader[:random.randint(4,7)]  # 4-7 items per trader
        self.active=False  # player is nearby

    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)

    def update(self):
        self.bob+=0.04
        if self.plat:
            p=self.plat
            if self.x<p.x: self.x=p.x
            if self.x+self.w>p.x+p.w: self.x=p.x+p.w-self.w

    def draw(self,surf,cx,cy):
        rx=int(self.x-cx);ry=int(self.y-cy)
        if rx+self.w<-40 or rx>WIDTH+40: return
        bob=int(math.sin(self.bob)*2)
        # Robe
        pygame.draw.rect(surf,(80,40,100),(rx,ry+10+bob,self.w,self.h-10))
        pygame.draw.rect(surf,(60,20,80), (rx,ry+10+bob,self.w,4))
        # Head
        pygame.draw.rect(surf,(220,180,140),(rx+3,ry+bob,14,12))
        # Hat
        pygame.draw.polygon(surf,(80,40,100),[(rx+2,ry+bob),(rx+18,ry+bob),(rx+10,ry-8+bob)])
        pygame.draw.rect(surf,(60,20,80),(rx,ry+bob,self.w,3))
        # Eyes
        pygame.draw.rect(surf,(255,255,200),(rx+5,ry+3+bob,3,3))
        pygame.draw.rect(surf,(255,255,200),(rx+12,ry+3+bob,3,3))
        # "T" label
        lbl=font_tiny.render("TRADE",True,(255,220,100))
        surf.blit(lbl,(rx+self.w//2-lbl.get_width()//2,ry-18+bob))
        # Interaction glow when active
        if self.active:
            alpha_rect(surf,(255,220,100),(rx-4,ry-4,self.w+8,self.h+8),int(30+20*math.sin(self.bob*3)))
            hint=font_tiny.render("[E] Trade",True,(255,220,100))
            surf.blit(hint,(rx+self.w//2-hint.get_width()//2,ry-30+bob))

# ─────────────────────────────────────────────────────────────────────────────
# Trial Pillar
# ─────────────────────────────────────────────────────────────────────────────
class TrialPillar:
    def __init__(self,x,y,plat):
        self.x=x;self.y=y;self.w=22;self.h=36;self.plat=plat
        self.bob=0;self.active=False;self.glow=0
        # Reward: trial-source items
        trial_items=[(k,v) for k,v in ITEMS.items() if "trial" in v["source"]]
        self.reward=random.choice(trial_items)[0] if trial_items else "golden_apple"
        self.completed=False
    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self): self.bob+=0.05; self.glow=(self.glow+1)%60
    def draw(self,surf,cx,cy):
        if self.completed: return
        rx=int(self.x-cx);ry=int(self.y-cy)
        if rx+self.w<-40 or rx>WIDTH+40: return
        pulse=int(80+60*math.sin(self.glow*0.1))
        pygame.draw.rect(surf,(40,20,80),(rx,ry,self.w,self.h))
        pygame.draw.rect(surf,(80,40,160),(rx+2,ry+2,self.w-4,self.h-4))
        alpha_rect(surf,(150,80,255),(rx,ry,self.w,self.h),pulse)
        # Rune symbol
        pygame.draw.line(surf,(200,150,255),(rx+11,ry+4),(rx+11,ry+32),2)
        pygame.draw.line(surf,(200,150,255),(rx+4,ry+14),(rx+18,ry+14),2)
        pygame.draw.line(surf,(200,150,255),(rx+4,ry+24),(rx+18,ry+24),2)
        if self.active:
            hint=font_tiny.render("[E] Trial",True,(200,150,255))
            surf.blit(hint,(rx+self.w//2-hint.get_width()//2,ry-20))
            rw=ITEMS[self.reward]
            rname=font_tiny.render(f"Reward: {rw['name']}",True,(180,120,255))
            surf.blit(rname,(rx+self.w//2-rname.get_width()//2,ry-32))

# ─────────────────────────────────────────────────────────────────────────────
# Relic Trial Pillar — blue, harder, rewards a relic
# ─────────────────────────────────────────────────────────────────────────────
class RelicPillar:
    def __init__(self,x,y,plat):
        self.x=x;self.y=y;self.w=24;self.h=42;self.plat=plat
        self.bob=0;self.active=False;self.glow=0;self.completed=False
        self.reward=random.choice(list(RELICS.keys()))
    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def update(self): self.bob+=0.04; self.glow=(self.glow+1)%60
    def draw(self,surf,cx,cy):
        if self.completed: return
        rx=int(self.x-cx);ry=int(self.y-cy)
        if rx+self.w<-40 or rx>WIDTH+40: return
        pulse=int(80+70*math.sin(self.glow*0.1))
        # Blue glowing pillar
        pygame.draw.rect(surf,(0,20,60),(rx,ry,self.w,self.h))
        pygame.draw.rect(surf,(20,60,180),(rx+2,ry+2,self.w-4,self.h-4))
        alpha_rect(surf,(60,140,255),(rx,ry,self.w,self.h),pulse)
        # Star/diamond rune
        cx2=rx+self.w//2; cy2=ry+self.h//2
        r=RELICS[self.reward]
        gem_col=r["gem"]
        pygame.draw.polygon(surf,gem_col,[(cx2,ry+4),(cx2+8,cy2),(cx2,ry+self.h-4),(cx2-8,cy2)])
        pygame.draw.polygon(surf,(min(255,gem_col[0]+80),min(255,gem_col[1]+80),min(255,gem_col[2]+80)),
                            [(cx2,ry+4),(cx2+8,cy2),(cx2,cy2),(cx2-8,cy2)])
        alpha_rect(surf,gem_col,(rx-4,ry-4,self.w+8,self.h+8),int(pulse*0.4))
        # "RELIC" label
        lbl=font_tiny.render("✦ RELIC",True,(80,180,255))
        surf.blit(lbl,(rx+self.w//2-lbl.get_width()//2,ry-12))
        if self.active:
            hint=font_tiny.render("[E] Relic Trial",True,(80,200,255))
            surf.blit(hint,(rx+self.w//2-hint.get_width()//2,ry-22))
            rname=font_tiny.render(f"★ {r['name']}",True,r["color"])
            surf.blit(rname,(rx+self.w//2-rname.get_width()//2,ry-34))
            rdesc=font_tiny.render(r["desc"],True,(80,140,200))
            surf.blit(rdesc,(rx+self.w//2-rdesc.get_width()//2,ry-46))

# ─────────────────────────────────────────────────────────────────────────────
# Enemy
# ─────────────────────────────────────────────────────────────────────────────
# Monster equipment: (weapon_key or None, armor_key or None)
MONSTER_GEAR_CHANCES = {
    "walker":      [("wood_sword",None,0.3),(None,"cloth",0.2),(None,None,0.5)],
    "archer":      [("wood_sword","leather",0.2),(None,"leather",0.3),(None,None,0.5)],
    "jumper":      [(None,None,1.0)],
    "bomber":      [(None,"leather",0.25),(None,None,0.75)],
    "knight":      [("iron_sword","chainmail",0.35),("gold_sword","plate",0.1),("iron_sword","leather",0.3),(None,"chainmail",0.25)],
    "ghost":       [(None,None,1.0)],
    "troll":       [(None,"leather",0.3),(None,"chainmail",0.15),(None,None,0.55)],
    "dark_archer": [(None,"leather",0.3),(None,None,0.7)],
    "slime":       [(None,None,1.0)],
    "ninja_e":     [("iron_sword",None,0.3),(None,None,0.7)],
}
# Drop chances by gear quality
GEAR_DROP_CHANCE = {None:0,"wood_sword":0.1,"iron_sword":0.3,"gold_sword":0.5,"shadow_blade":0.7,
                    "cloth":0.05,"leather":0.2,"chainmail":0.4,"plate":0.65}

class Enemy:
    def __init__(self,x,y,plat,etype="walker"):
        self.x=x;self.y=y;self.w=18;self.h=28;self.vy=0
        self.plat=plat;self.on_ground=False;self.type=etype
        self.dead=False;self.death_timer=25;self.facing_right=True;self.anim_tick=0
        self.invincible=0
        if etype=="walker":  self.vx=1.3;self.hp=1;self.max_hp=1;self.shoot_cd=99999
        elif etype=="archer":self.vx=0;  self.hp=2;self.max_hp=2;self.shoot_cd=160
        elif etype=="jumper":self.vx=0;  self.hp=1;self.max_hp=1;self.shoot_cd=99999;self.jump_cd=80;self.jump_warn=0
        elif etype=="bomber":self.vx=0.6;self.hp=2;self.max_hp=2;self.shoot_cd=99999;self.bomb_cd=200;self.bomb_warn=0
        elif etype=="knight":self.vx=0.8;self.hp=4;self.max_hp=4;self.shoot_cd=99999;self.shield_up=True
        elif etype=="ghost":
            self.vx=1.5;self.hp=2;self.max_hp=2;self.shoot_cd=99999
            self.float_offset=random.uniform(0,math.pi*2)  # for floating bob
            self.phase_alpha=200  # ghost transparency pulsing
        elif etype=="troll":
            self.vx=0.6;self.hp=8;self.max_hp=8;self.shoot_cd=99999
            self.w=28;self.h=36  # bigger body
            self.charge_cd=0;self.charging=False
        elif etype=="dark_archer":
            self.vx=0;self.hp=3;self.max_hp=3;self.shoot_cd=140
            self.arrow_cd=0  # fires homing arrows
        elif etype=="slime":
            self.vx=random.choice([-0.8,0.8]);self.hp=2;self.max_hp=2;self.shoot_cd=99999
            self.is_mini=False  # spawns 2 mini slimes on death
        elif etype=="ninja_e":
            self.vx=2.5;self.hp=3;self.max_hp=3;self.shoot_cd=99999
            self.dash_cd=0;self.dash_timer=0;self.on_wall=False;self.wall_dir=0
            self.coyote=0
        else:                self.vx=1.3;self.hp=1;self.max_hp=1;self.shoot_cd=99999
        # Roll gear
        chances=MONSTER_GEAR_CHANCES.get(etype,[("",None,1.0)])
        r=random.random(); acc=0
        self.weapon_item=None; self.armor_item=None
        for wk,ak,chance in chances:
            acc+=chance
            if r<acc:
                self.weapon_item=wk if wk else None
                self.armor_item=ak if ak else None
                break
        # Buff stats based on gear
        if self.weapon_item: self.hp+=ITEMS[self.weapon_item]["dmg"]-1
        if self.armor_item:  self.hp+=ITEMS[self.armor_item]["def"]
        self.max_hp=self.hp
        # Currency value: base 8-15 + gear bonus
        self.gold_value=random.randint(8,15)
        if self.weapon_item: self.gold_value+=ITEMS[self.weapon_item]["price"]//3+5
        if self.armor_item:  self.gold_value+=ITEMS[self.armor_item]["price"]//3+4

    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def is_shielded_from(self,ax):
        if self.type!="knight" or not self.shield_up: return False
        return ax<self.x if self.facing_right else ax>self.x+self.w

    def get_drops(self):
        drops=[]
        for key in [self.weapon_item,self.armor_item]:
            if key and random.random()<GEAR_DROP_CHANCE.get(key,0):
                drops.append(key)
        return drops

    def update(self, all_platforms=None):
        if self.dead: self.death_timer-=1; return self.death_timer>0
        if self.invincible>0: self.invincible-=1
        self.anim_tick+=1
        # Ghosts ignore gravity — handle movement separately
        if self.type=="ghost":
            self.x+=self.vx
            self.on_ground=False
        else:
            self.vy+=GRAVITY; self.x+=self.vx; self.y+=self.vy
            self.on_ground=False  # reset every frame

        # Check assigned platform first, then fall back to all platforms
        plats_to_check = [self.plat] if self.plat else []
        if all_platforms:
            plats_to_check = all_platforms

        for p in plats_to_check:
            if p is None: continue
            if p.type=="drop": continue
            # Only snap to top of platform
            if (self.y+self.h >= p.y and self.y+self.h <= p.y+p.h+8
                    and self.x+self.w > p.x+2 and self.x < p.x+p.w-2
                    and self.vy >= 0):
                self.y=p.y-self.h; self.vy=0; self.on_ground=True
                self.plat=p  # reassign to whichever platform we're standing on
                break

        # Patrol bounds on current platform
        if self.plat and self.on_ground:
            if self.x < self.plat.x: self.vx=abs(self.vx); self.facing_right=True
            if self.x+self.w > self.plat.x+self.plat.w: self.vx=-abs(self.vx); self.facing_right=False

        if self.type=="archer" and self.on_ground: self.vx*=0.85; self.shoot_cd-=1
        if self.type=="dark_archer" and self.on_ground: self.vx*=0.88; self.shoot_cd-=1
        if self.type=="jumper" and self.on_ground:
            self.jump_cd-=1
            if self.jump_cd<=20: self.jump_warn=1
            if self.jump_cd<=0: self.vy=-10;self.jump_cd=random.randint(60,120);self.jump_warn=0;self.vx=random.choice([-3,3])
        if self.type=="bomber":
            self.vx*=0.95
            if self.on_ground: self.bomb_cd-=1
            if self.bomb_cd<=30: self.bomb_warn=1
            if self.bomb_cd<=0: self.bomb_cd=random.randint(150,250);self.bomb_warn=0
        if self.type=="ghost":
            # Float above platforms — ignore gravity, oscillate up/down
            self.vy=0
            self.float_offset+=0.05
            self.phase_alpha=int(120+80*math.sin(self.float_offset*1.3))
            # Find nearest platform below ghost if plat not set
            if not self.plat and all_platforms:
                best=None; best_dist=999
                for p in all_platforms:
                    if p.y>self.y and abs(p.x+p.w/2-self.x)<p.w/2+20:
                        d=p.y-self.y
                        if d<best_dist: best_dist=d; best=p
                if best: self.plat=best
            # Reverse direction at platform edges
            if self.plat:
                if self.x<self.plat.x: self.vx=abs(self.vx); self.facing_right=True
                if self.x+self.w>self.plat.x+self.plat.w: self.vx=-abs(self.vx); self.facing_right=False
                self.y=self.plat.y-self.h-10+math.sin(self.float_offset)*8
            else:
                # No platform found — gentle hover in place
                self.y+=math.sin(self.float_offset)*0.5
        if self.type=="troll":
            # Slow walk, but charges when player nearby (handled in game update)
            if self.on_ground: self.vx=math.copysign(0.6,self.vx)
            self.charge_cd=max(0,self.charge_cd-1)
        if self.type=="slime":
            # Bounce along ground, change direction randomly
            if self.on_ground and random.random()<0.01: self.vx*=-1
            if self.on_ground and abs(self.vx)<0.3: self.vx=random.choice([-0.8,0.8])
        if self.type=="ninja_e":
            # Wall slide
            if self.dash_cd>0: self.dash_cd-=1
            if self.dash_timer>0: self.dash_timer-=1
        return True

    def draw(self,surf,cx,cy,accent):
        rx=int(self.x-cx);ry=int(self.y-cy)
        if rx+self.w<-40 or rx>WIDTH+40: return
        t=self.death_timer/25 if self.dead else 1.0
        alpha=int(255*t);
        if alpha<=0: return
        COLS={"walker":((100,22,22),(150,38,38)),"archer":((70,22,100),(105,38,150)),
              "jumper":((22,80,22),(38,130,38)),"bomber":((100,60,10),(160,90,15)),
              "knight":((50,50,70),(80,80,110))}
        bc,hc=COLS.get(self.type,((80,22,22),(120,38,38)))
        ec=(255,255,255) if self.invincible>0 else (255,70,70)
        if self.dead:
            ang=(1-t)*300
            tmp=pygame.Surface((self.w+6,self.h+6),pygame.SRCALPHA)
            pygame.draw.rect(tmp,(*bc,alpha),(2,10,self.w,self.h-10))
            pygame.draw.rect(tmp,(*hc,alpha),(4,0,12,10))
            rot=pygame.transform.rotate(tmp,ang)
            surf.blit(rot,(rx-rot.get_width()//2+self.w//2,ry-rot.get_height()//2+self.h//2)); return
        bob=int(math.sin(self.anim_tick*0.08)*1.5)
        # Armor tint
        if self.armor_item:
            ac=ITEMS[self.armor_item]["color"]
            alpha_rect(surf,ac,(rx-1,ry+7+bob,self.w+2,self.h-7),60)

        if self.type=="walker":
            # Red grunt — basic rectangular enemy
            pygame.draw.rect(surf,(110,25,25),(rx,ry+8+bob,self.w,self.h-8))
            pygame.draw.rect(surf,(160,45,45),(rx+2,ry+bob,14,11))
            pygame.draw.rect(surf,ec,(rx+3,ry+2+bob,4,3)); pygame.draw.rect(surf,ec,(rx+9,ry+2+bob,4,3))
            alpha_rect(surf,ec,(rx+3,ry+2+bob,4,3),70); alpha_rect(surf,ec,(rx+9,ry+2+bob,4,3),70)
            # Angry brow
            pygame.draw.line(surf,(80,0,0),(rx+3,ry+1+bob),(rx+7,ry+3+bob),2)
            pygame.draw.line(surf,(80,0,0),(rx+9,ry+3+bob),(rx+13,ry+1+bob),2)

        elif self.type=="archer":
            # Purple mage-style with pointed hat
            pygame.draw.rect(surf,(70,22,100),(rx,ry+8+bob,self.w,self.h-8))
            pygame.draw.rect(surf,(100,35,150),(rx+2,ry+bob,14,11))
            pygame.draw.rect(surf,ec,(rx+3,ry+2+bob,4,3)); pygame.draw.rect(surf,ec,(rx+9,ry+2+bob,4,3))
            alpha_rect(surf,ec,(rx+3,ry+2+bob,4,3),70); alpha_rect(surf,ec,(rx+9,ry+2+bob,4,3),70)
            # Pointed hat
            pygame.draw.polygon(surf,(50,15,80),[(rx+4,ry+bob),(rx+14,ry+bob),(rx+9,ry-9+bob)])
            pygame.draw.rect(surf,(60,20,90),(rx+2,ry+bob,14,3))
            # Bow
            bx=rx+(self.w+2 if self.facing_right else -12)
            pygame.draw.arc(surf,(160,120,30),(bx-4,ry+self.h//2-11+bob,16,22),math.radians(260),math.radians(100),2)
            pygame.draw.line(surf,(200,180,100),(bx+4,ry+self.h//2-11+bob),(bx+4,ry+self.h//2+11+bob),1)

        elif self.type=="jumper":
            # Green frog-like with big round head
            pygame.draw.rect(surf,(20,100,30),(rx+1,ry+10+bob,self.w-2,self.h-10))
            # Big round head
            pygame.draw.circle(surf,(30,140,40),(rx+self.w//2,ry+5+bob),10)
            # Big bulging eyes
            pygame.draw.circle(surf,(200,255,200),(rx+4,ry+2+bob),5)
            pygame.draw.circle(surf,(200,255,200),(rx+14,ry+2+bob),5)
            pygame.draw.circle(surf,(0,0,0),(rx+5,ry+2+bob),2)
            pygame.draw.circle(surf,(0,0,0),(rx+15,ry+2+bob),2)
            # Legs (spread when jumping)
            leg_spread=4 if not self.on_ground else 0
            pygame.draw.rect(surf,(20,100,30),(rx-leg_spread,ry+self.h-6+bob,8,6))
            pygame.draw.rect(surf,(20,100,30),(rx+self.w-8+leg_spread,ry+self.h-6+bob,8,6))
            if self.jump_warn:
                alpha_rect(surf,(38,200,38),(rx,ry+bob,self.w,self.h),int(80+70*math.sin(self.anim_tick*0.3)))

        elif self.type=="bomber":
            # Orange demolitions expert with big bomb belly
            pygame.draw.rect(surf,(100,60,10),(rx,ry+8+bob,self.w,self.h-8))
            pygame.draw.rect(surf,(140,80,15),(rx+2,ry+bob,14,11))
            pygame.draw.rect(surf,ec,(rx+3,ry+2+bob,4,3)); pygame.draw.rect(surf,ec,(rx+9,ry+2+bob,4,3))
            alpha_rect(surf,ec,(rx+3,ry+2+bob,4,3),70); alpha_rect(surf,ec,(rx+9,ry+2+bob,4,3),70)
            # Big round bomb belly
            pygame.draw.circle(surf,(30,30,30),(rx+self.w//2,ry+16+bob),8)
            pygame.draw.circle(surf,(50,50,50),(rx+self.w//2-2,ry+14+bob),3)
            # Fuse on head
            pygame.draw.line(surf,(200,160,0),(rx+self.w//2,ry+bob),(rx+self.w//2+4,ry-5+bob),2)
            if self.bomb_warn:
                pulse=int(200+55*math.sin(self.anim_tick*0.4))
                pygame.draw.circle(surf,(pulse,pulse//3,0),(rx+self.w//2,ry+16+bob),8)
                alpha_rect(surf,(255,80,0),(rx,ry+bob,self.w,self.h),int(80+80*math.sin(self.anim_tick*0.4)))

        elif self.type=="knight":
            # Silver armored knight — wide and imposing
            pygame.draw.rect(surf,(55,55,75),(rx-1,ry+7+bob,self.w+2,self.h-7))  # body armour
            pygame.draw.rect(surf,(80,80,110),(rx,ry+bob,self.w,11))              # full helmet
            pygame.draw.rect(surf,(110,110,150),(rx+1,ry+bob,self.w-2,4))         # visor shine
            # T-visor slit
            pygame.draw.rect(surf,(0,0,20),(rx+3,ry+4+bob,12,3))
            # Shoulder pauldrons
            pygame.draw.rect(surf,(90,90,120),(rx-3,ry+7+bob,5,8))
            pygame.draw.rect(surf,(90,90,120),(rx+self.w-2,ry+7+bob,5,8))
            # Front shield
            if self.shield_up:
                sx5=rx+(self.w if self.facing_right else -10)
                pygame.draw.rect(surf,(70,100,150),(sx5,ry+6+bob,10,20))
                pygame.draw.rect(surf,(110,150,210),(sx5+1,ry+7+bob,4,10))
                alpha_rect(surf,(100,140,200),(sx5-1,ry+5+bob,12,22),60)
                # Cross on shield
                pygame.draw.line(surf,(130,180,255),(sx5+5,ry+8+bob),(sx5+5,ry+24+bob),1)
                pygame.draw.line(surf,(130,180,255),(sx5+2,ry+16+bob),(sx5+8,ry+16+bob),1)

        elif self.type=="ghost":
            # Translucent floating wisp — cyan/white
            ga=getattr(self,'phase_alpha',160)
            ghost_surf=pygame.Surface((self.w+8,self.h+8),pygame.SRCALPHA)
            # Cloak body
            pygame.draw.ellipse(ghost_surf,(150,220,255,ga),(2,self.h//3,self.w+4,self.h*2//3+4))
            # Head
            pygame.draw.ellipse(ghost_surf,(200,240,255,ga),(4,0,self.w,self.h//2))
            # Glowing eyes
            eye_col=(255,255,255,min(255,ga+50))
            pygame.draw.circle(ghost_surf,eye_col,(self.w//2-4,self.h//5),4)
            pygame.draw.circle(ghost_surf,eye_col,(self.w//2+4,self.h//5),4)
            pygame.draw.circle(ghost_surf,(0,0,80,200),(self.w//2-4,self.h//5),2)
            pygame.draw.circle(ghost_surf,(0,0,80,200),(self.w//2+4,self.h//5),2)
            # Trailing wisps at bottom
            for wi in range(3):
                wx2=int(self.w*0.2+wi*self.w*0.3)
                wy2=self.h+2+int(math.sin(self.float_offset+wi)*4)
                pygame.draw.circle(ghost_surf,(150,220,255,ga//2),(wx2,wy2),3)
            surf.blit(ghost_surf,(rx-4,ry-4))

        elif self.type=="troll":
            # Big grey-green tank
            pygame.draw.rect(surf,(50,90,50),(rx,ry+self.h//4+bob,self.w,self.h*3//4))
            # Round head
            pygame.draw.ellipse(surf,(70,110,60),(rx+2,ry+bob,self.w-4,self.h//3+4))
            # Thick brow ridge
            pygame.draw.rect(surf,(40,70,40),(rx+2,ry+bob+4,self.w-4,4))
            # Small angry eyes
            eye_c=(255,80,0) if self.invincible>0 else (200,50,0)
            pygame.draw.rect(surf,eye_c,(rx+5,ry+bob+8,5,4))
            pygame.draw.rect(surf,eye_c,(rx+self.w-10,ry+bob+8,5,4))
            # Tusks
            pygame.draw.rect(surf,(220,200,160),(rx+6,ry+bob+self.h//3,4,6))
            pygame.draw.rect(surf,(220,200,160),(rx+self.w-10,ry+bob+self.h//3,4,6))
            # Arms
            pygame.draw.rect(surf,(50,90,50),(rx-8,ry+self.h//4+bob,10,self.h//3))
            pygame.draw.rect(surf,(50,90,50),(rx+self.w-2,ry+self.h//4+bob,10,self.h//3))
            # Charge glow
            if getattr(self,'charging',False):
                alpha_rect(surf,(255,150,0),(rx-4,ry-4,self.w+8,self.h+8),
                           int(60+40*math.sin(self.anim_tick*0.3)))

        elif self.type=="dark_archer":
            # Hooded dark figure
            pygame.draw.rect(surf,(20,20,40),(rx,ry+8+bob,self.w,self.h-8))
            pygame.draw.rect(surf,(30,30,55),(rx+2,ry+bob,14,11))
            # Hood (dark triangle)
            pygame.draw.polygon(surf,(15,15,35),
                [(rx+2,ry+bob),(rx+16,ry+bob),(rx+9,ry-8+bob)])
            pygame.draw.rect(surf,(20,20,40),(rx+1,ry+bob,16,5))
            # Glowing red eyes (no pupils visible — just red slits)
            pygame.draw.rect(surf,(200,20,20),(rx+4,ry+3+bob,5,2))
            pygame.draw.rect(surf,(200,20,20),(rx+10,ry+3+bob,5,2))
            alpha_rect(surf,(255,0,0),(rx+3,ry+2+bob,7,4),80)
            alpha_rect(surf,(255,0,0),(rx+9,ry+2+bob,7,4),80)
            # Dark bow with glow
            bx=rx+(self.w+2 if self.facing_right else -12)
            pygame.draw.arc(surf,(80,0,150),(bx-4,ry+self.h//2-11+bob,16,22),
                            math.radians(260),math.radians(100),2)
            alpha_rect(surf,(120,0,200),(bx-6,ry+self.h//2-13+bob,20,26),30)

        elif self.type=="slime":
            # Blob — circle body, wobble animation
            wobble=int(math.sin(self.anim_tick*0.12)*2)
            col=(40,180,40) if not getattr(self,'is_mini',False) else (60,220,60)
            r2=9 if not self.is_mini else 5
            pygame.draw.ellipse(surf,col,(rx-wobble,ry+self.h-r2*2+bob,self.w+wobble*2,r2*2))
            # Shiny top
            pygame.draw.ellipse(surf,(100,230,100),(rx+3,ry+self.h-r2*2+2+bob,self.w-6,r2-2))
            # Eyes
            eye_y=ry+self.h-r2*2+r2//2+bob
            pygame.draw.circle(surf,(0,0,0),(rx+self.w//2-3,eye_y),2)
            pygame.draw.circle(surf,(0,0,0),(rx+self.w//2+3,eye_y),2)
            pygame.draw.circle(surf,(255,255,255),(rx+self.w//2-2,eye_y-1),1)
            pygame.draw.circle(surf,(255,255,255),(rx+self.w//2+4,eye_y-1),1)

        elif self.type=="ninja_e":
            # Enemy ninja — dark outfit, red headband
            pygame.draw.rect(surf,(20,20,30),(rx+2,ry+9+bob,14,15))  # body
            pygame.draw.rect(surf,(20,20,30),(rx+3,ry+bob,12,11))    # head
            pygame.draw.rect(surf,(180,30,30),(rx+3,ry+3+bob,12,4))  # red headband
            # Eyes
            ex2=rx+9 if self.facing_right else rx+4
            pygame.draw.rect(surf,(255,80,80),(ex2,ry+1+bob,5,3))
            # Scarf
            sc_x=rx-4 if self.facing_right else rx+self.w
            alpha_rect(surf,(180,30,30),(sc_x,ry+5+bob,5,3),140)
            # Sword
            sx2=rx+self.w+1 if self.facing_right else rx-11
            pygame.draw.rect(surf,(120,120,120),(sx2,ry+9+bob,10,2))
            pygame.draw.rect(surf,(200,200,200),(sx2+1,ry+9+bob,7,1))
            # Dash glow when dashing
            if getattr(self,'dash_timer',0)>0:
                alpha_rect(surf,(180,30,30),(rx-4,ry-2,self.w+8,self.h+4),80)
        # Weapon glint for geared enemies
        if self.weapon_item:
            wc=ITEMS[self.weapon_item]["color"]
            wx6=rx+(self.w+1 if self.facing_right else -8)
            pygame.draw.line(surf,wc,(wx6,ry+8+bob),(wx6+(8 if self.facing_right else -8),ry+14+bob),2)
        if self.hp<self.max_hp:
            pygame.draw.rect(surf,(25,25,25),(rx,ry-10,self.w,5))
            pygame.draw.rect(surf,(226,75,74),(rx,ry-10,int(self.w*self.hp/self.max_hp),5))

# ─────────────────────────────────────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self,x,y):
        self.x=x;self.y=y;self.w=20;self.h=26
        self.vx=0.0;self.vy=0.0
        self.on_ground=False;self.on_wall=False;self.wall_dir=0;self.coyote=0
        self.facing_right=True
        self.dash_cd=0;self.dash_timer=0;self.dash_dir=1
        self.invincible=0;self.slash_cd=0;self.slash_anim=0
        self.ammo=8;self.throw_cd=0
        self.run_tick=0;self.jump_squat=0
        # Shield: hold C, max 2s, then 3s cooldown
        self.shield=False;self.shield_timer=0;self.shield_cd=0
        SHIELD_MAX_FRAMES=120   # 2 seconds at 60fps
        self.SHIELD_MAX=SHIELD_MAX_FRAMES
        self.SHIELD_CD=180      # 3 second cooldown
        # RPG stats
        self.hp=MAX_HP;self.max_hp=MAX_HP
        self.gold=0
        self.regen_timer=0       # frames of regen remaining
        self.effects={}          # effect_name -> frames remaining
        # Equipment
        self.weapon="wood_sword"
        self.armor="cloth"
        # Inventory: dict of item_key -> count
        self.inventory={}
        # Hotbar slots 1-5 for consumables
        self.hotbar=[None,None,None,None,None]
        self.selected_slot=0
        self.last_pickup_msg=""; self.last_pickup_timer=0
        # Relics — max 3 passive slots
        self.relics=[]          # list of relic keys (max 3)
        self.slash_count=0      # for phantom_edge every-5th-slash
        self.revived=False      # soul_lantern one-time revive
        self.void_step_hit=set()# enemies hit during current dash

    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)
    def shield_rect(self):
        if self.facing_right: return pygame.Rect(self.x+self.w,self.y-4,18,self.h+8)
        else:                  return pygame.Rect(self.x-18,self.y-4,18,self.h+8)

    def has_relic(self,key): return key in self.relics

    def equip_relic(self,key):
        if key in self.relics: return False
        if len(self.relics)>=3: return False
        self.relics.append(key)
        if key=="dragon_heart": self.max_hp+=5; self.hp=min(self.hp+5,self.max_hp)
        if key=="quiver": self.ammo=min(16,self.ammo)
        return True

    @property
    def max_ammo(self): return 16 if self.has_relic("quiver") else 8

    def add_item(self,key):
        self.inventory[key]=self.inventory.get(key,0)+1
        self.last_pickup_msg=f"Got: {ITEMS[key]['name']}"
        self.last_pickup_timer=120
        # Auto-equip weapon/armor only if slot is empty (starting defaults)
        if ITEMS[key]["cat"]=="weapon" and self.weapon=="wood_sword":
            self.weapon=key
            self.last_pickup_msg=f"Equipped {ITEMS[key]['name']}!"
        elif ITEMS[key]["cat"]=="armor" and self.armor=="cloth":
            self.armor=key
            self.last_pickup_msg=f"Equipped {ITEMS[key]['name']}!"
        # Auto-add consumables to hotbar
        if ITEMS[key]["cat"] in("food","potion"):
            for i,slot in enumerate(self.hotbar):
                if slot is None:
                    self.hotbar[i]=key; break
                elif slot==key:
                    break

    def use_hotbar(self,slot_idx):
        key=self.hotbar[slot_idx]
        if not key or self.inventory.get(key,0)<=0: return
        data=ITEMS[key]
        if data["cat"] in("food","potion"):
            hp_gained=0
            if data.get("hp",0)>0:
                old=self.hp; self.hp=min(self.max_hp,self.hp+data["hp"]); hp_gained=self.hp-old
            eff=data.get("effect")
            if eff:
                dur=data.get("dur",300)
                if eff=="regen" and self.has_relic("medic_bag"): dur=int(dur*2)
                self.effects[eff]=dur
                if eff=="regen": self.regen_timer=dur
            self.inventory[key]-=1
            if self.inventory[key]<=0:
                del self.inventory[key]
                self.hotbar[slot_idx]=None
            msg=f"Used {data['name']}!"
            if hp_gained>0: msg+=f" +{hp_gained}HP"
            if eff: msg+=f" [{eff.upper()}]"
            self.last_pickup_msg=msg; self.last_pickup_timer=100

    @property
    def slash_dmg(self):
        base=ITEMS.get(self.weapon,{}).get("dmg",1)
        if "power" in self.effects:
            bonus=2
            for k in self.inventory:
                if ITEMS.get(k,{}).get("effect")=="power" and "power_bonus" in ITEMS.get(k,{}):
                    bonus=max(bonus,ITEMS[k]["power_bonus"])
            base+=bonus
        if self.has_relic("berserker_tooth"): base+=max(0,(self.combo//3))
        return base

    @property
    def defense(self):
        base=int(ITEMS.get(self.armor,{}).get("def",0))
        if "barrier" in self.effects: base+=2
        if self.has_relic("iron_will"): base+=1
        if self.has_relic("last_stand") and self.hp<=3: base+=2
        return base

    @property
    def move_speed(self):
        if "speed" in self.effects: return SPEED*1.55
        return SPEED

    def draw(self,surf,cx,cy,accent):
        invisible="invis" in self.effects
        if self.invincible>0 and (self.invincible//4)%2==1: return
        if invisible and (pygame.time.get_ticks()//80)%3!=0: return  # flicker when invisible

        rx=int(self.x-cx);ry=int(self.y-cy);fr=self.facing_right
        SKIN=(255,205,155);HAIR=(35,22,8)
        SC=tuple(min(255,int(c*0.55+45)) for c in accent)
        SS=tuple(max(0,c-35) for c in SC)
        SHORTS=(25,45,95);SHOE=(28,28,28);SOLE=(215,215,215)
        WHITE=(255,255,255);PUPIL=(20,20,70)

        # Effect tints
        if "power" in self.effects: alpha_rect(surf,(255,80,0),(rx-4,ry-4,self.w+8,self.h+8),50)
        if "speed" in self.effects: alpha_rect(surf,(80,200,255),(rx-4,ry-4,self.w+8,self.h+8),40)
        if "barrier" in self.effects: alpha_rect(surf,(100,160,255),(rx-6,ry-6,self.w+12,self.h+12),int(40+20*math.sin(pygame.time.get_ticks()*0.01)))

        bob=int(math.sin(self.run_tick*0.35)*2) if self.on_ground and abs(self.vx)>0.5 else 0
        sy=int(-3 if self.jump_squat>0 else 0)
        sx2=int(2 if self.jump_squat>0 else 0)
        ry2=ry+bob+sy

        # Shadow
        shd=pygame.Surface((self.w+8,6),pygame.SRCALPHA)
        pygame.draw.ellipse(shd,(0,0,0,55),(0,0,self.w+8,6))
        surf.blit(shd,(rx-4,ry+self.h+1))

        bw=self.w-2+sx2*2
        # Legs
        pygame.draw.rect(surf,SHORTS,(rx+2,ry2+16,6,5));pygame.draw.rect(surf,SKIN,(rx+2,ry2+21,6,4))
        pygame.draw.rect(surf,SHOE,(rx+1,ry2+24,7,3));pygame.draw.rect(surf,SOLE,(rx+1,ry2+26,7,1))
        pygame.draw.rect(surf,SHORTS,(rx+12,ry2+16,6,5));pygame.draw.rect(surf,SKIN,(rx+12,ry2+21,6,4))
        pygame.draw.rect(surf,SHOE,(rx+11+sx2,ry2+24,7,3));pygame.draw.rect(surf,SOLE,(rx+11+sx2,ry2+26,7,1))
        # Armor tint on body
        arm_col=ITEMS.get(self.armor,{}).get("color",SC)
        pygame.draw.rect(surf,arm_col,(rx+1-sx2,ry2+10,bw,8))
        pygame.draw.rect(surf,SS,(rx+1-sx2,ry2+16,bw,2))
        pygame.draw.rect(surf,arm_col,(rx+5,ry2+9,10,2))
        if fr:
            pygame.draw.rect(surf,arm_col,(rx+bw-1,ry2+10,5,4));pygame.draw.rect(surf,SKIN,(rx+bw-1,ry2+14,5,5))
            pygame.draw.rect(surf,SKIN,(rx-3,ry2+11,4,7))
        else:
            pygame.draw.rect(surf,arm_col,(rx-4,ry2+10,5,4));pygame.draw.rect(surf,SKIN,(rx-4,ry2+14,5,5))
            pygame.draw.rect(surf,SKIN,(rx+self.w-1,ry2+11,4,7))
        # Head
        pygame.draw.rect(surf,SKIN,(rx+3,ry2+1,14,11))
        ex=rx+15 if fr else rx+3; pygame.draw.rect(surf,SKIN,(ex,ry2+5,2,4))
        if fr:
            pygame.draw.rect(surf,WHITE,(rx+11,ry2+3,5,4));pygame.draw.rect(surf,PUPIL,(rx+13,ry2+4,2,2))
            pygame.draw.rect(surf,WHITE,(rx+5,ry2+3,4,3)); pygame.draw.rect(surf,PUPIL,(rx+6,ry2+4,2,2))
        else:
            pygame.draw.rect(surf,WHITE,(rx+4,ry2+3,5,4)); pygame.draw.rect(surf,PUPIL,(rx+4,ry2+4,2,2))
            pygame.draw.rect(surf,WHITE,(rx+11,ry2+3,4,3));pygame.draw.rect(surf,PUPIL,(rx+12,ry2+4,2,2))
        brow=rx+11 if fr else rx+5; pygame.draw.rect(surf,HAIR,(brow,ry2+2,5,1))
        mx=rx+11 if fr else rx+5;  pygame.draw.rect(surf,(185,100,85),(mx,ry2+8,4,1))
        # Hair
        pygame.draw.rect(surf,HAIR,(rx+3,ry2,14,4));pygame.draw.rect(surf,HAIR,(rx+3,ry2,3,8));pygame.draw.rect(surf,HAIR,(rx+14,ry2,3,6))
        for sx3,sy3,sw3,sh3 in [(rx+5,ry2-5,4,5),(rx+9,ry2-7,4,7),(rx+13,ry2-4,3,4)]:
            pygame.draw.rect(surf,HAIR,(sx3,sy3,sw3,sh3)); pygame.draw.rect(surf,(65,45,18),(sx3+1,sy3,2,1))
        # Weapon
        wc=ITEMS.get(self.weapon,{}).get("color",(160,160,160))
        swing=int(math.sin(self.slash_anim/14*math.pi)*8) if self.slash_anim>0 else 0
        if fr:
            bx=rx+self.w+1
            pygame.draw.rect(surf,(105,60,18),(bx,ry2+10,4,6))
            pygame.draw.rect(surf,(145,75,18),(bx-1,ry2+8,6,3))
            pygame.draw.rect(surf,wc,(bx+2,ry2+4-swing,14,3))
            pygame.draw.rect(surf,(min(255,wc[0]+60),min(255,wc[1]+60),min(255,wc[2]+60)),(bx+2,ry2+4-swing,14,1))
        else:
            bx=rx-14
            pygame.draw.rect(surf,(105,60,18),(bx+10,ry2+10,4,6))
            pygame.draw.rect(surf,(145,75,18),(bx+11,ry2+8,6,3))
            pygame.draw.rect(surf,wc,(bx,ry2+4+swing,14,3))
        # Dash glow
        if self.dash_timer>0: alpha_rect(surf,accent,(rx-6,ry-3,self.w+12,self.h+6),int(self.dash_timer/9*120))
        # Wall cling
        if self.on_wall and not self.on_ground:
            wx=rx+self.w if self.wall_dir>0 else rx-4; alpha_rect(surf,accent,(wx,ry+4,4,self.h-8),200)
        # Shield
        if self.shield:
            pct=1-(self.shield_timer/self.SHIELD_MAX)
            sx4=rx+self.w+1 if self.facing_right else rx-12
            pygame.draw.rect(surf,(100,160,255),(sx4,ry+2,10,self.h-4))
            pygame.draw.rect(surf,(180,210,255),(sx4+2,ry+2,3,self.h-4))
            alpha_rect(surf,(100,160,255),(sx4-2,ry,14,self.h+4),60)
            # Durability crack overlay
            if pct>0.5: alpha_rect(surf,(255,0,0),(sx4,ry+2,10,self.h-4),int(pct*80))

# ─────────────────────────────────────────────────────────────────────────────
# Background
# ─────────────────────────────────────────────────────────────────────────────
class Background:
    def __init__(self):
        self.stars=[(random.randint(0,WIDTH),random.randint(0,int(HEIGHT*0.8)),
                     random.choice([1,1,1,2]),random.uniform(0.05,0.3)) for _ in range(140)]
        self.clouds=[(random.uniform(0,5000),random.uniform(20,HEIGHT*0.4),
                      random.randint(60,200),random.uniform(0.04,0.12)) for _ in range(20)]
        self.ambient_particles=[]
        self.ambient_tick=0

    def update(self, biome, cam_x):
        self.ambient_tick+=1
        # Spawn ambient particles based on biome
        if self.ambient_tick%8==0 and len(self.ambient_particles)<60:
            pt=biome["ptcl_type"]
            col=biome["ptcl"]
            px=cam_x+random.randint(0,WIDTH)
            if pt=="leaf":
                self.ambient_particles.append(
                    {"x":px,"y":random.randint(-20,HEIGHT//2),"vx":random.uniform(-0.5,-1.5),
                     "vy":random.uniform(0.3,1.0),"rot":random.uniform(0,6),"rspd":random.uniform(-0.05,0.05),
                     "col":col,"type":pt,"life":1.0})
            elif pt=="ember":
                self.ambient_particles.append(
                    {"x":px,"y":HEIGHT+10,"vx":random.uniform(-1,1),
                     "vy":random.uniform(-2,-4),"rot":0,"rspd":0,
                     "col":col,"type":pt,"life":1.0})
            elif pt=="drip":
                self.ambient_particles.append(
                    {"x":px,"y":random.randint(0,HEIGHT//2),"vx":random.uniform(-0.2,0.2),
                     "vy":random.uniform(1.5,3),"rot":0,"rspd":0,
                     "col":col,"type":pt,"life":1.0})
            elif pt=="star":
                self.ambient_particles.append(
                    {"x":px,"y":random.randint(0,HEIGHT),"vx":random.uniform(-0.3,0.3),
                     "vy":random.uniform(-0.2,0.2),"rot":0,"rspd":0,
                     "col":col,"type":pt,"life":random.uniform(0.5,1.0)})
        # Update ambient particles
        to_rm=[]
        for i,p in enumerate(self.ambient_particles):
            p["x"]+=p["vx"]; p["y"]+=p["vy"]
            p["rot"]+=p["rspd"]
            p["life"]-=0.006
            if p["life"]<=0 or p["y"]>HEIGHT+40 or p["y"]<-40: to_rm.append(i)
        for i in reversed(to_rm): self.ambient_particles.pop(i)

    def draw(self, surf, cam_x, cam_y, biome):
        bg_top=biome["bg_top"]; bg_bot=biome["bg_bot"]
        mtn_col=biome["mtn_col"]

        # Sky gradient
        for row in range(0,HEIGHT,3):
            t=row/HEIGHT; r=int(bg_top[0]+(bg_bot[0]-bg_top[0])*t)
            g=int(bg_top[1]+(bg_bot[1]-bg_top[1])*t); b=int(bg_top[2]+(bg_bot[2]-bg_top[2])*t)
            pygame.draw.rect(surf,(r,g,b),(0,row,WIDTH,3))

        # Stars — more prominent in Cave/Space
        if biome["name"] in("Cave","Space"):
            for sx,sy,sz,par in self.stars:
                px=int((sx-cam_x*par)%WIDTH)
                if biome["name"]=="Space":
                    c=random.randint(180,255) if sz>1 else 120
                    pygame.draw.rect(surf,(c,c,min(255,c+40)),(px,sy,sz,sz))
                else:
                    pygame.draw.rect(surf,(255,255,255),(px,sy,sz,sz))

        # Biome-specific background elements
        if biome["name"]=="Forest":
            # Tree silhouettes
            self._mtn(surf,cam_x*0.15,mtn_col,HEIGHT*0.58,180,0.006)
            nc=tuple(min(255,c+18) for c in mtn_col)
            self._mtn(surf,cam_x*0.35+500,nc,HEIGHT*0.70,110,0.010)
            self._trees(surf, cam_x*0.2, mtn_col, HEIGHT*0.55)
            # Clouds
            for cx4,cy4,cw,par in self.clouds:
                px3=int((cx4-cam_x*par)%(WIDTH+400))-200
                alpha_rect(surf,(255,255,255),(px3,int(cy4),cw,22),11)
                alpha_rect(surf,(255,255,255),(px3+12,int(cy4)-10,cw-24,18),9)

        elif biome["name"]=="Cave":
            # Dark rocky ceiling
            self._stalactites(surf, cam_x*0.3, mtn_col)
            self._mtn(surf,cam_x*0.15,mtn_col,HEIGHT*0.6,160,0.008)
            # Crystal glow patches
            for i in range(8):
                cx2=int((i*310-cam_x*0.25)%(WIDTH+200))-100
                alpha_rect(surf,biome["ptcl"],(cx2,HEIGHT-60,40,60),
                           int(20+15*math.sin(self.ambient_tick*0.04+i)))

        elif biome["name"]=="Volcano":
            # Lava glow at horizon
            for gy2 in range(0,6):
                alpha_rect(surf,(255,80,0),(0,HEIGHT-20+gy2*4,WIDTH,6),
                           int(15+10*math.sin(self.ambient_tick*0.03)))
            self._mtn(surf,cam_x*0.15,mtn_col,HEIGHT*0.55,220,0.006)
            nc2=tuple(min(255,c+25) for c in mtn_col)
            self._mtn(surf,cam_x*0.35+500,nc2,HEIGHT*0.70,130,0.009)
            # Lava cracks in bg
            for i in range(5):
                cx3=int((i*240-cam_x*0.2)%(WIDTH+200))-100
                alpha_rect(surf,(255,100,0),(cx3,HEIGHT//2,8,HEIGHT//2),
                           int(10+8*math.sin(self.ambient_tick*0.05+i)))

        elif biome["name"]=="Space":
            # Nebula clouds
            for i in range(6):
                nx=int((i*350-cam_x*0.08)%(WIDTH+400))-200
                ny=int(HEIGHT*0.1+i*40)
                alpha_rect(surf,biome["ptcl"],(nx,ny,200,80),
                           int(8+5*math.sin(self.ambient_tick*0.02+i)))
            # Large distant stars
            for i in range(20):
                sx2=int((i*179+cam_x*0.05)%WIDTH)
                sy2=(i*97+33)%(HEIGHT*3//4)
                r2=1 if i%3 else 2
                c2=int(150+80*math.sin(self.ambient_tick*0.03+i))
                pygame.draw.rect(surf,(c2,c2,255),(sx2,sy2,r2,r2))

        # Ambient biome particles (leaves, embers, drips, stars, fireflies)
        for p in self.ambient_particles:
            px2=int(p["x"]-cam_x*0.6); py2=int(p["y"])
            alpha=int(p["life"]*200)
            col=p["col"]
            pt=p["type"]
            if pt=="leaf":
                s2=pygame.Surface((8,5),pygame.SRCALPHA)
                pygame.draw.ellipse(s2,(*col,alpha),(0,0,8,5))
                rot_s=pygame.transform.rotate(s2,math.degrees(p["rot"]))
                surf.blit(rot_s,(px2-4,py2-2))
            elif pt=="ember":
                pygame.draw.circle(surf,(*col,alpha),(px2,py2),2)
                alpha_rect(surf,col,(px2-3,py2-3,6,6),alpha//3)
            elif pt=="drip":
                pygame.draw.rect(surf,(*col,alpha),(px2,py2,2,6))
            elif pt=="star":
                c3=int(p["life"]*255)
                pygame.draw.rect(surf,(c3,c3,255),(px2,py2,2,2))

        # Ground fog
        for i in range(5):
            alpha_rect(surf,bg_bot,(0,HEIGHT-30+i*7,WIDTH,10),40+i*14)

    def _mtn(self,surf,offset,color,base_y,amp,freq):
        pts=[(0,HEIGHT)]
        for px in range(0,WIDTH+20,8):
            wx=px+offset
            py=base_y-amp*(0.5*math.sin(wx*freq)+0.3*math.sin(wx*freq*2.1+1.2)+0.2*math.sin(wx*freq*3.7+2.4))
            pts.append((px,int(py)))
        pts.append((WIDTH,HEIGHT))
        if len(pts)>2: pygame.draw.polygon(surf,color,pts)

    def _trees(self,surf,offset,color,base_y):
        tc=tuple(min(255,c+20) for c in color)
        for i in range(0,WIDTH+60,55):
            tx=int((i-offset)%((WIDTH+60)))-30
            th=random.randint(40,80) if not hasattr(self,'_tree_h') else self._tree_h
            pygame.draw.rect(surf,color,(tx+10,int(base_y)-20,6,25))
            pygame.draw.polygon(surf,tc,[(tx,int(base_y)-20),(tx+26,int(base_y)-20),(tx+13,int(base_y)-60)])

    def _stalactites(self,surf,offset,color):
        c2=tuple(min(255,c+20) for c in color)
        for i in range(0,WIDTH+80,45):
            sx=int((i-offset)%(WIDTH+80))-40
            sh=random.randint(20,55) if not hasattr(self,'_stal_h') else 35
            pygame.draw.polygon(surf,c2,[(sx,0),(sx+20,0),(sx+10,sh)])

# ─────────────────────────────────────────────────────────────────────────────
# UI: Shop overlay
# ─────────────────────────────────────────────────────────────────────────────
class ShopUI:
    def __init__(self):
        self.open=False;self.trader=None;self.selected=0;self.msg="";self.msg_timer=0
    def show(self,trader): self.open=True;self.trader=trader;self.selected=0
    def close(self): self.open=False;self.trader=None
    def draw(self,surf,player):
        if not self.open or not self.trader: return
        has_eye=player.has_relic("merchant_eye")
        pw=560;ph=420;px=WIDTH//2-pw//2;py=HEIGHT//2-ph//2
        pygame.draw.rect(surf,(10,8,22),(px,py,pw,ph))
        pygame.draw.rect(surf,(80,40,160),(px,py,pw,ph),2)
        alpha_rect(surf,(80,40,160),(px,py,pw,ph),15)
        title="TRADER  SHOP" + ("  [Merchant's Eye: -20%]" if has_eye else "")
        t=font_med.render(title,True,(200,150,255) if not has_eye else (220,180,255))
        surf.blit(t,(px+pw//2-t.get_width()//2,py+12))
        g=font_small.render(f"Your Gold: {player.gold}",True,(255,220,80))
        surf.blit(g,(px+pw-g.get_width()-14,py+12))
        pygame.draw.line(surf,(60,30,100),(px+10,py+42),(px+pw-10,py+42),1)
        # Merchant eye shows up to 9 items instead of 7
        stock=self.trader.stock[:9] if has_eye else self.trader.stock
        for i,(k,v) in enumerate(stock):
            iy=py+54+i*42; sel=i==self.selected
            real_price=max(1,int(v["price"]*0.8)) if has_eye else v["price"]
            can_afford=player.gold>=real_price
            if sel: pygame.draw.rect(surf,(40,20,80),(px+6,iy,pw-12,38)); pygame.draw.rect(surf,(100,50,200),(px+6,iy,pw-12,38),1)
            pygame.draw.rect(surf,v["color"],(px+14,iy+8,18,18))
            pygame.draw.rect(surf,(255,255,255),(px+14,iy+8,18,18),1)
            nc=(255,220,100) if sel else (180,160,220) if can_afford else (100,80,100)
            ns=font_small.render(v["name"],True,nc); surf.blit(ns,(px+38,iy+3))
            ds=font_tiny.render(v["desc"],True,(100,80,140) if can_afford else (60,40,60)); surf.blit(ds,(px+38,iy+19))
            price_col=(100,220,100) if can_afford else (220,80,80)
            if has_eye and v["price"]>0:
                old=font_tiny.render(f"{v['price']}g",True,(100,60,60))
                surf.blit(old,(px+pw-old.get_width()-14,iy+2))
                ps=font_small.render(f"{real_price}g",True,(100,255,100)); surf.blit(ps,(px+pw-ps.get_width()-14,iy+14))
            else:
                ps=font_small.render(f"{real_price}g",True,price_col); surf.blit(ps,(px+pw-ps.get_width()-14,iy+10))
            if not can_afford:
                need=font_tiny.render(f"need {real_price-player.gold}g",True,(150,60,60))
                surf.blit(need,(px+pw-need.get_width()-14,iy+28))
            owned=player.inventory.get(k,0)
            if owned>0 and can_afford:
                os2=font_tiny.render(f"x{owned}",True,(80,200,80)); surf.blit(os2,(px+pw-os2.get_width()-55,iy+28))
        ch=font_tiny.render("↑↓ Select   E/Enter=Buy   Esc=Close",True,(60,40,100))
        surf.blit(ch,(px+pw//2-ch.get_width()//2,py+ph-22))
        if self.msg_timer>0:
            self.msg_timer-=1
            mc=font_small.render(self.msg,True,(255,220,100)); surf.blit(mc,(px+pw//2-mc.get_width()//2,py+ph-44))

    def handle_key(self,key,player):
        if not self.open: return
        if key==pygame.K_ESCAPE: self.close(); return
        has_eye=player.has_relic("merchant_eye")
        stock=self.trader.stock[:9] if has_eye else self.trader.stock
        if key==pygame.K_UP: self.selected=max(0,self.selected-1)
        if key==pygame.K_DOWN: self.selected=min(len(stock)-1,self.selected+1)
        if key in(pygame.K_e,pygame.K_RETURN,pygame.K_KP_ENTER):
            k,v=stock[self.selected]
            real_price=max(1,int(v["price"]*0.8)) if has_eye else v["price"]
            if player.gold>=real_price:
                player.gold-=real_price; player.add_item(k)
                self.msg=f"Bought {v['name']}!"; self.msg_timer=90
            else:
                self.msg="Not enough gold!"; self.msg_timer=90

# ─────────────────────────────────────────────────────────────────────────────
# UI: Inventory overlay
# ─────────────────────────────────────────────────────────────────────────────
class InvUI:
    def __init__(self):
        self.open=False; self.selected=0; self.msg=""; self.msg_timer=0
        self.COLS=3; self.ROWS=3; self.MAX_SLOTS=9
        # Store panel geometry for mouse hit-testing (set during draw)
        self.px=0;self.py=0;self.pw=580;self.ph=480
        self.SLOT_W=118;self.SLOT_H=70;self.GRID_X=0;self.GRID_Y=0
        self.HB_X=0;self.HB_Y=0;self.HB_W=100;self.HB_H=48

    def _slot_rect(self,slot_i):
        col=slot_i%self.COLS; row=slot_i//self.COLS
        sx=self.GRID_X+col*(self.SLOT_W+4); sy=self.GRID_Y+row*(self.SLOT_H+4)
        return pygame.Rect(sx,sy,self.SLOT_W,self.SLOT_H)

    def _hotbar_rect(self,i):
        hx=self.px+14+i*108; hy=self.HB_Y+4
        return pygame.Rect(hx,hy,self.HB_W,self.HB_H)

    def handle_mouse(self,pos,button,player):
        """button: 1=left click (select/use), 3=right click (equip/send to hotbar)"""
        if not self.open: return
        items_list=list(player.inventory.items())
        # Check inventory grid slots
        for slot_i in range(self.MAX_SLOTS):
            if self._slot_rect(slot_i).collidepoint(pos):
                self.selected=slot_i
                if button==1 and slot_i<len(items_list):
                    # Left click = select (single click) or double-click to use
                    # We'll do: left click = select, right click = use/equip
                    pass
                elif button==3 and slot_i<len(items_list):
                    # Right click = use/equip immediately
                    self._use_selected(player, items_list)
                return
        # Check hotbar slots
        for i in range(5):
            if self._hotbar_rect(i).collidepoint(pos):
                if button==1:
                    # Left click hotbar = use it
                    player.use_hotbar(i)
                    self.msg=f"Used slot {i+1}"; self.msg_timer=60
                elif button==3:
                    # Right click hotbar = clear slot
                    player.hotbar[i]=None
                    self.msg=f"Cleared slot {i+1}"; self.msg_timer=60
                return

    def _use_selected(self,player,items_list=None):
        if items_list is None: items_list=list(player.inventory.items())
        n=len(items_list)
        if not(0<=self.selected<n): return
        k,cnt=items_list[self.selected]
        data=ITEMS[k]
        if data["cat"] in("food","potion") and cnt>0:
            if data.get("hp",0)>0: player.hp=min(player.max_hp,player.hp+data["hp"])
            eff=data.get("effect")
            if eff:
                dur=data.get("dur",300)
                if eff=="regen" and player.has_relic("medic_bag"): dur=int(dur*2)
                player.effects[eff]=dur
                if eff=="regen": player.regen_timer=dur
            player.inventory[k]-=1
            if player.inventory[k]<=0:
                del player.inventory[k]
                # Also clear from hotbar if this was the last one
                for hi,hs in enumerate(player.hotbar):
                    if hs==k: player.hotbar[hi]=None
                self.selected=max(0,self.selected-1)
            self.msg=f"Used {data['name']}! +{data.get('hp',0)}HP"; self.msg_timer=90
        elif data["cat"]=="weapon":
            player.weapon=k; self.msg=f"Equipped {data['name']}!"; self.msg_timer=90
        elif data["cat"]=="armor":
            player.armor=k; self.msg=f"Equipped {data['name']}!"; self.msg_timer=90

    def draw(self,surf,player):
        if not self.open: return
        pw=580;ph=480;px=WIDTH//2-pw//2;py=HEIGHT//2-ph//2
        # Save geometry for mouse hit-testing
        self.px=px;self.py=py;self.pw=pw;self.ph=ph
        SLOT_W=118;SLOT_H=70;GRID_X=px+180;GRID_Y=py+42
        self.SLOT_W=SLOT_W;self.SLOT_H=SLOT_H;self.GRID_X=GRID_X;self.GRID_Y=GRID_Y
        HB_Y=py+ph-90; self.HB_Y=HB_Y

        mouse_pos=pygame.mouse.get_pos()

        pygame.draw.rect(surf,(8,12,22),(px,py,pw,ph))
        pygame.draw.rect(surf,(40,80,160),(px,py,pw,ph),2)
        alpha_rect(surf,(40,80,160),(px,py,pw,ph),12)
        surf.blit(font_med.render("INVENTORY",True,(133,183,235)),(px+pw//2-50,py+10))

        # ── Equipment panel (left strip) ─────────────────────────────────────
        pygame.draw.rect(surf,(15,25,45),(px+10,py+42,160,130))
        pygame.draw.rect(surf,(30,50,80),(px+10,py+42,160,130),1)
        surf.blit(font_tiny.render("EQUIPPED",True,(80,100,140)),(px+14,py+46))
        wn=ITEMS.get(player.weapon,{}).get("name","None")
        an=ITEMS.get(player.armor,{}).get("name","None")
        wc=ITEMS.get(player.weapon,{}).get("color",(160,160,160))
        ac=ITEMS.get(player.armor,{}).get("color",(160,140,120))
        pygame.draw.rect(surf,wc,(px+14,py+62,18,18)); pygame.draw.rect(surf,(255,255,255),(px+14,py+62,18,18),1)
        surf.blit(font_small.render(f"⚔ {wn}",True,wc),(px+36,py+64))
        pygame.draw.rect(surf,ac,(px+14,py+86,18,18)); pygame.draw.rect(surf,(255,255,255),(px+14,py+86,18,18),1)
        surf.blit(font_small.render(f"🛡 {an}",True,ac),(px+36,py+88))
        surf.blit(font_tiny.render(f"DMG +{ITEMS.get(player.weapon,{}).get('dmg',1)}",True,(239,159,39)),(px+14,py+110))
        surf.blit(font_tiny.render(f"DEF +{int(ITEMS.get(player.armor,{}).get('def',0))}",True,(133,183,235)),(px+14,py+124))
        surf.blit(font_small.render(f"Gold: {player.gold}",True,(255,220,80)),(px+14,py+144))
        # Active effects
        ey=py+162
        for eff,frames in player.effects.items():
            if frames>0:
                ec2=(80,200,255) if eff=="speed" else (255,100,0) if eff=="power" else (100,160,255) if eff=="barrier" else (180,120,255) if eff=="invis" else (80,220,120)
                surf.blit(font_tiny.render(f"◆ {eff.upper()} {frames//60}s",True,ec2),(px+14,ey)); ey+=14

        # ── 9-slot grid (3×3) ────────────────────────────────────────────────
        items_list=list(player.inventory.items())  # [(key,count), ...]

        surf.blit(font_tiny.render("ITEMS  — click to select  right-click to use/equip",True,(60,80,120)),(GRID_X,GRID_Y-14))

        for slot_i in range(self.MAX_SLOTS):
            sr=self._slot_rect(slot_i)
            sx,sy=sr.x,sr.y
            sel=slot_i==self.selected
            hovered=sr.collidepoint(mouse_pos)
            # Background
            bg=(30,45,70) if sel else (22,32,50) if hovered else (14,20,35)
            pygame.draw.rect(surf,bg,(sx,sy,SLOT_W,SLOT_H))
            # Border — green if equipped, yellow if selected, cyan if hovered, dim otherwise
            if slot_i<len(items_list):
                k,cnt=items_list[slot_i]
                is_equipped=(k==player.weapon or k==player.armor)
                if is_equipped:          border_col=(80,200,80)
                elif sel:                border_col=(200,180,60)
                elif hovered:            border_col=(80,180,220)
                else:                    border_col=(35,55,80)
                pygame.draw.rect(surf,border_col,(sx,sy,SLOT_W,SLOT_H),2 if sel or is_equipped or hovered else 1)
                v=ITEMS[k]
                # Color swatch
                pygame.draw.rect(surf,v["color"],(sx+5,sy+5,28,28))
                pygame.draw.rect(surf,(255,255,255),(sx+5,sy+5,28,28),1)
                # Category icon inside swatch
                cat=v["cat"]
                if cat=="weapon": pygame.draw.line(surf,(255,255,255),(sx+8,sy+28),(sx+28,sy+8),2)
                elif cat=="armor": pygame.draw.polygon(surf,(255,255,255),[(sx+17,sy+7),(sx+29,sy+12),(sx+29,sy+22),(sx+17,sy+29),(sx+5,sy+22),(sx+5,sy+12)])
                elif cat in("food","potion"): pygame.draw.circle(surf,(255,255,255),(sx+17,sy+17),6,2)
                # Name & desc
                nc=(255,230,120) if sel else (200,200,255) if hovered else (180,180,220)
                surf.blit(font_tiny.render(v["name"],True,nc),(sx+37,sy+5))
                surf.blit(font_tiny.render(v["desc"][:18],True,(70,80,110)),(sx+5,sy+38))
                # Count
                surf.blit(font_tiny.render(f"x{cnt}",True,(200,200,100)),(sx+SLOT_W-28,sy+5))
                # EQUIPPED badge
                if is_equipped:
                    surf.blit(font_tiny.render("EQUIP",True,(80,200,80)),(sx+SLOT_W-42,sy+SLOT_H-16))
                # Tooltip on hover
                if hovered and not sel:
                    tip=f"L-click=select  R-click={'use' if v['cat'] in ('food','potion') else 'equip'}"
                    ts=font_tiny.render(tip,True,(160,200,255)); surf.blit(ts,(sx,sy-14))
            else:
                pygame.draw.rect(surf,(25,35,50) if hovered else (20,28,42),(sx,sy,SLOT_W,SLOT_H),1)
                surf.blit(font_tiny.render("empty",True,(30,40,55)),(sx+SLOT_W//2-16,sy+SLOT_H//2-6))

        # ── Hotbar row ────────────────────────────────────────────────────────
        pygame.draw.line(surf,(30,50,80),(px+10,HB_Y-10),(px+pw-10,HB_Y-10),1)
        surf.blit(font_tiny.render("HOTBAR — H=send selected here  L-click=use  R-click=clear",True,(60,80,120)),(px+14,HB_Y-8))
        for i,slot in enumerate(player.hotbar):
            hr=self._hotbar_rect(i); hx,hy=hr.x,hr.y
            is_cur=i==player.selected_slot
            hov=hr.collidepoint(mouse_pos)
            bg2=(25,35,60) if hov else (15,22,40)
            pygame.draw.rect(surf,bg2,(hx,hy,100,48))
            bcol2=(255,220,80) if is_cur else (80,180,220) if hov else (35,55,80)
            pygame.draw.rect(surf,bcol2,(hx,hy,100,48),2 if is_cur or hov else 1)
            surf.blit(font_tiny.render(str(i+1),True,(100,100,140)),(hx+4,hy+3))
            if slot and slot in ITEMS:
                v2=ITEMS[slot]
                pygame.draw.rect(surf,v2["color"],(hx+28,hy+10,24,24))
                surf.blit(font_tiny.render(v2["name"][:7],True,(180,180,200)),(hx+4,hy+32))
                cnt2=player.inventory.get(slot,0)
                surf.blit(font_tiny.render(f"x{cnt2}",True,(200,200,100)),(hx+80,hy+3))
                if hov:
                    surf.blit(font_tiny.render("click=use",True,(160,200,255)),(hx,hy-14))
            else:
                surf.blit(font_tiny.render("empty",True,(30,40,55)),(hx+28,hy+18))

        # Message feedback
        if self.msg_timer>0:
            self.msg_timer-=1
            ms=font_small.render(self.msg,True,(255,220,100))
            surf.blit(ms,(px+pw//2-ms.get_width()//2,py+ph-18))
        else:
            surf.blit(font_tiny.render("E=Use/Equip  H=→Hotbar  D/Del=Drop  Arrows/Click=Navigate  Esc=Close",True,(45,55,80)),(px+pw//2-230,py+ph-18))

    def handle_key(self,key,player):
        if not self.open: return
        if key==pygame.K_ESCAPE: self.open=False; return
        items_list=list(player.inventory.items())
        n=len(items_list)
        # Arrow navigation in 3×3 grid
        if key==pygame.K_LEFT:  self.selected=max(0,self.selected-1)
        if key==pygame.K_RIGHT: self.selected=min(max(0,n-1),self.selected+1)
        if key==pygame.K_UP:    self.selected=max(0,self.selected-self.COLS)
        if key==pygame.K_DOWN:  self.selected=min(max(0,n-1),self.selected+self.COLS)
        # E or Enter = use/equip selected
        if key in(pygame.K_e,pygame.K_RETURN,pygame.K_KP_ENTER):
            self._use_selected(player,items_list)
        # H = move selected item to next free hotbar slot
        if key==pygame.K_h:
            if 0<=self.selected<n:
                k,_=items_list[self.selected]
                if ITEMS[k]["cat"] in("food","potion"):
                    placed=False
                    for i,slot in enumerate(player.hotbar):
                        if slot is None or slot==k:
                            player.hotbar[i]=k; placed=True
                            self.msg=f"→ Hotbar slot {i+1}"; self.msg_timer=80; break
                    if not placed:
                        player.hotbar[0]=k; self.msg=f"→ Hotbar slot 1 (replaced)"; self.msg_timer=80
                else:
                    self.msg="Only food/potions go in hotbar"; self.msg_timer=80
        # D / Delete / Backspace = drop one of selected item
        if key in(pygame.K_d, pygame.K_DELETE, pygame.K_BACKSPACE):
            if 0<=self.selected<n:
                k,cnt=items_list[self.selected]
                if k==player.weapon:
                    self.msg="Unequip weapon first!"; self.msg_timer=80
                elif k==player.armor and k!="cloth":
                    self.msg="Unequip armor first!"; self.msg_timer=80
                else:
                    player.inventory[k]-=1
                    if player.inventory[k]<=0:
                        del player.inventory[k]
                        for hi,hs in enumerate(player.hotbar):
                            if hs==k: player.hotbar[hi]=None
                        self.selected=max(0,self.selected-1)
                        self.msg=f"Dropped {ITEMS[k]['name']}"; self.msg_timer=80
                    else:
                        self.msg=f"Dropped 1x {ITEMS[k]['name']}"; self.msg_timer=80
        # 1-5 uses hotbar directly
        for i in range(5):
            if key==getattr(pygame,f"K_{i+1}"): player.use_hotbar(i)

# ─────────────────────────────────────────────────────────────────────────────
# Trial overlay
# ─────────────────────────────────────────────────────────────────────────────
class TrialUI:
    def __init__(self):
        self.open=False;self.pillar=None;self.enemies_to_kill=0
        self.killed=0;self.timer=0;self.spawned=[];self.is_relic=False
    def start(self,pillar):
        self.open=True;self.pillar=pillar;self.killed=0;self.is_relic=False
        self.enemies_to_kill=random.randint(3,5);self.timer=2400;self.spawned=[]
    def draw(self,surf):
        if not self.open: return
        if self.is_relic:
            # Blue relic trial banner — taller
            H=56
            pygame.draw.rect(surf,(0,10,40),(0,0,WIDTH,H))
            alpha_rect(surf,(40,120,255),(0,0,WIDTH,H),35)
            pygame.draw.line(surf,(60,140,255),(0,H-1),(WIDTH,H-1),1)
            rkey=self.pillar.reward if self.pillar else ""
            rname=RELICS[rkey]["name"] if rkey in RELICS else "?"
            t1=font_med.render(f"✦ RELIC TRIAL — Kill {self.enemies_to_kill} enemies",True,(80,200,255))
            surf.blit(t1,(WIDTH//2-t1.get_width()//2,4))
            t2=font_small.render(f"{self.killed}/{self.enemies_to_kill}   Time: {self.timer//60}s   Reward: {rname}",True,(60,160,220))
            surf.blit(t2,(WIDTH//2-t2.get_width()//2,28))
            pw2=340; pfill=int(pw2*self.killed/max(1,self.enemies_to_kill))
            pygame.draw.rect(surf,(0,20,60),(WIDTH//2-pw2//2,46,pw2,8))
            pygame.draw.rect(surf,(60,180,255),(WIDTH//2-pw2//2,46,pfill,8))
        else:
            # Purple normal trial banner — taller
            H=52
            pygame.draw.rect(surf,(20,0,40),(0,0,WIDTH,H))
            alpha_rect(surf,(150,80,255),(0,0,WIDTH,H),30)
            pygame.draw.line(surf,(100,50,180),(0,H-1),(WIDTH,H-1),1)
            t1=font_med.render(f"TRIAL — Kill {self.enemies_to_kill} enemies",True,(200,150,255))
            surf.blit(t1,(WIDTH//2-t1.get_width()//2,4))
            t2=font_small.render(f"Kills: {self.killed}/{self.enemies_to_kill}   Time remaining: {self.timer//60}s",True,(150,100,220))
            surf.blit(t2,(WIDTH//2-t2.get_width()//2,28))
            pw2=320; pfill=int(pw2*self.killed/max(1,self.enemies_to_kill))
            pygame.draw.rect(surf,(30,10,60),(WIDTH//2-pw2//2,44,pw2,6))
            pygame.draw.rect(surf,(150,80,255),(WIDTH//2-pw2//2,44,pfill,6))

# ─────────────────────────────────────────────────────────────────────────────
# Boss enemies — 3 types, each at score milestones
# ─────────────────────────────────────────────────────────────────────────────
BOSS_DATA = {
    "golem":  {"name":"Stone Golem",  "hp":60,  "color":(100,90,80),  "col2":(140,130,120),"gold":150,"score":1000,
               "w":48,"h":52,"desc":"Slow but devastating. Ground slam shakes the whole platform."},
    "shadow": {"name":"Shadow Lord",  "hp":90,  "color":(60,20,120),  "col2":(100,50,200), "gold":220,"score":2000,
               "w":44,"h":50,"desc":"Teleports, fires triple shurikens. Shield-immune."},
    "dragon": {"name":"Dragon King",  "hp":140, "color":(180,60,20),  "col2":(240,100,30), "gold":350,"score":3000,
               "w":60,"h":56,"desc":"Flies, breathes fire, stomps platforms. The final boss."},
}

class Boss:
    def __init__(self, x, y, btype, plat):
        self.x=x; self.y=y; self.btype=btype; self.plat=plat
        d=BOSS_DATA[btype]
        self.w=d["w"]; self.h=d["h"]
        self.hp=d["hp"]; self.max_hp=d["hp"]
        self.vx=0; self.vy=0; self.on_ground=False
        self.invincible=0; self.dead=False; self.death_timer=60
        self.anim_tick=0; self.facing_right=True
        self.phase=1       # phase 2 at 50% hp
        self.attack_cd=0
        self.enraged=False  # flashes red below 25% hp
        # Boss-specific state
        self.slam_charge=0; self.slam_warning=False   # golem
        self.teleport_cd=0; self.triple_cd=0          # shadow
        self.fly_timer=0; self.breathe_cd=0           # dragon
        self.projectiles=[]  # boss projectiles: {x,y,vx,vy,w,h,dmg,color}

    def rect(self): return pygame.Rect(self.x,self.y,self.w,self.h)

    def update(self, all_platforms, player):
        if self.dead: self.death_timer-=1; return self.death_timer>0
        if self.invincible>0: self.invincible-=1
        self.anim_tick+=1
        if self.hp<=0:
            self.dead=True
            return True
        # Phase 2 at 50% hp
        if self.hp<=self.max_hp//2 and self.phase==1:
            self.phase=2
        self.enraged=self.hp<=self.max_hp//4
        if self.attack_cd>0: self.attack_cd-=1
        self.facing_right=player.x>self.x
        new_proj=[]

        if self.btype=="golem":
            self._update_golem(all_platforms, player, new_proj)
        elif self.btype=="shadow":
            self._update_shadow(all_platforms, player, new_proj)
        elif self.btype=="dragon":
            self._update_dragon(all_platforms, player, new_proj)

        self.projectiles=new_proj+[p for p in self.projectiles if self._move_proj(p)]
        return True

    def _move_proj(self, p):
        p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=0.15
        p["life"]=p.get("life",200)-1
        return p["life"]>0 and p["y"]<DEATH_Y

    def _update_golem(self, plats, player, new_proj):
        # Walk slowly toward player
        spd=0.8 if self.phase==1 else 1.3
        self.vx=math.copysign(spd,player.x-self.x) if abs(player.x-self.x)>30 else 0
        self.vy+=GRAVITY; self.x+=self.vx; self.y+=self.vy
        self.on_ground=False
        for p in plats:
            if p.type=="drop": continue
            if(self.y+self.h>=p.y and self.y+self.h<=p.y+p.h+10
               and self.x+self.w>p.x and self.x<p.x+p.w and self.vy>=0):
                self.y=p.y-self.h; self.vy=0; self.on_ground=True; break
        # Ground slam attack
        if self.on_ground and self.attack_cd==0:
            self.slam_charge+=1
            if self.slam_charge>40: self.slam_warning=True
            if self.slam_charge>70:
                # SLAM — create shockwave projectiles both sides
                self.slam_warning=False; self.slam_charge=0
                cd=90 if self.phase==1 else 55
                self.attack_cd=cd
                for dx in [-12,-6,6,12]:
                    new_proj.append({"x":self.x+self.w/2,"y":self.y+self.h-4,
                                     "vx":dx*0.9,"vy":-3,"w":14,"h":14,"dmg":4,"color":(150,130,100),"life":80})
        else:
            self.slam_charge=0; self.slam_warning=False
        if self.phase==2 and self.attack_cd==0:
            # Jump slam
            if self.on_ground: self.vy=JUMP_V*0.85; self.attack_cd=80

    def _update_shadow(self, plats, player, new_proj):
        self.vy+=GRAVITY; self.y+=self.vy; self.x+=self.vx; self.vx*=0.85
        self.on_ground=False
        for p in plats:
            if p.type=="drop": continue
            if(self.y+self.h>=p.y and self.y+self.h<=p.y+p.h+10
               and self.x+self.w>p.x and self.x<p.x+p.w and self.vy>=0):
                self.y=p.y-self.h; self.vy=0; self.on_ground=True; break
        # Teleport near player periodically
        if self.teleport_cd>0: self.teleport_cd-=1
        else:
            self.teleport_cd=200 if self.phase==1 else 120
            # Teleport to near player
            self.x=player.x+random.choice([-160,160]); self.y=player.y-50
        # Triple shuriken burst
        if self.triple_cd>0: self.triple_cd-=1
        elif self.attack_cd==0:
            self.triple_cd=100 if self.phase==1 else 60; self.attack_cd=20
            dx=player.x-(self.x+self.w/2); dy=player.y-(self.y+self.h/2)
            dist=max(1,math.hypot(dx,dy))
            for ang in [-0.3,0,0.3]:
                vx=dx/dist*9*math.cos(ang)-dy/dist*9*math.sin(ang)
                vy=dy/dist*9*math.cos(ang)+dx/dist*9*math.sin(ang)
                new_proj.append({"x":self.x+self.w/2,"y":self.y+self.h/2,
                                 "vx":vx,"vy":vy,"w":10,"h":10,"dmg":3,"color":(150,50,255),"life":150})

    def _update_dragon(self, plats, player, new_proj):
        # Dragon flies and swoops
        if self.fly_timer>0:
            self.fly_timer-=1
            # Fly toward player
            tx=player.x-self.w/2; ty=player.y-100
            self.x+=(tx-self.x)*0.04; self.y+=(ty-self.y)*0.04
            self.vy=0
        else:
            self.vy+=GRAVITY*0.6; self.y+=self.vy; self.x+=self.vx; self.vx*=0.92
            self.on_ground=False
            for p in plats:
                if p.type=="drop": continue
                if(self.y+self.h>=p.y and self.y+self.h<=p.y+p.h+10
                   and self.x+self.w>p.x and self.x<p.x+p.w and self.vy>=0):
                    self.y=p.y-self.h; self.vy=0; self.on_ground=True; break
            if self.on_ground and self.attack_cd==0:
                self.fly_timer=120 if self.phase==1 else 80; self.attack_cd=50
        # Fire breath — stream of fire orbs
        if self.breathe_cd>0: self.breathe_cd-=1
        elif self.attack_cd==0:
            self.breathe_cd=20 if self.phase==1 else 12; self.attack_cd=5
            d=1 if self.facing_right else -1
            spread=random.uniform(-1.5,1.5)
            new_proj.append({"x":self.x+(self.w if d>0 else 0),"y":self.y+self.h*0.4,
                             "vx":d*8,"vy":spread,"w":16,"h":16,"dmg":3,"color":(255,120,20),"life":80})

    def draw(self, surf, cx, cy, accent):
        rx=int(self.x-cx); ry=int(self.y-cy)
        if rx+self.w<-80 or rx>WIDTH+80: return
        d=BOSS_DATA[self.btype]
        bc=d["color"]; bc2=d["col2"]
        t=self.death_timer/60 if self.dead else 1.0
        if t<=0: return
        # Death spin
        if self.dead:
            tmp=pygame.Surface((self.w+4,self.h+4),pygame.SRCALPHA)
            pygame.draw.rect(tmp,(*bc,int(255*t)),(0,self.h//4,self.w,self.h*3//4))
            pygame.draw.ellipse(tmp,(*bc2,int(255*t)),(4,0,self.w-8,self.h//2))
            rot=pygame.transform.rotate(tmp,(1-t)*360)
            surf.blit(rot,(rx-rot.get_width()//2+self.w//2,ry-rot.get_height()//2+self.h//2))
            return
        # Enrage flash
        if self.enraged and self.anim_tick%8<4:
            alpha_rect(surf,(255,50,50),(rx-4,ry-4,self.w+8,self.h+8),80)

        if self.btype=="golem":
            # Rocky body
            pygame.draw.rect(surf,bc,(rx,ry+self.h//3,self.w,self.h*2//3))
            pygame.draw.rect(surf,bc,(rx+4,ry,self.w-8,self.h//2))
            pygame.draw.rect(surf,bc2,(rx+6,ry+2,self.w-12,self.h//4))
            # Cracked lines
            pygame.draw.line(surf,(60,50,40),(rx+10,ry+self.h//3),(rx+22,ry+self.h-8),2)
            pygame.draw.line(surf,(60,50,40),(rx+self.w-14,ry+8),(rx+self.w-6,ry+self.h//2),2)
            # Eyes glow
            ec=(255,200,50) if not self.slam_warning else (255,50,50)
            pygame.draw.circle(surf,ec,(rx+14,ry+self.h//4),5)
            pygame.draw.circle(surf,ec,(rx+self.w-14,ry+self.h//4),5)
            alpha_rect(surf,ec,(rx+9,ry+self.h//4-5,10,10),60)
            alpha_rect(surf,ec,(rx+self.w-19,ry+self.h//4-5,10,10),60)
            # Slam warning
            if self.slam_warning:
                pw2=int(self.slam_charge/70*100)
                pygame.draw.rect(surf,(60,30,20),(rx,ry-12,100,6))
                pygame.draw.rect(surf,(255,100,0),(rx,ry-12,pw2,6))
                alpha_rect(surf,(255,50,0),(rx-4,ry-4,self.w+8,self.h+8),
                           int(40*math.sin(self.anim_tick*0.3)))
            # Arms
            pygame.draw.rect(surf,bc,(rx-10,ry+self.h//4,12,self.h//2))
            pygame.draw.rect(surf,bc,(rx+self.w-2,ry+self.h//4,12,self.h//2))

        elif self.btype=="shadow":
            # Shadowy cloaked figure
            cloak_pulse=int(40+30*math.sin(self.anim_tick*0.06))
            pygame.draw.rect(surf,bc,(rx+4,ry+self.h//3,self.w-8,self.h*2//3))
            pygame.draw.ellipse(surf,bc,(rx,ry,self.w,self.h//2))
            alpha_rect(surf,bc2,(rx-6,ry-6,self.w+12,self.h+12),cloak_pulse)
            # Glowing purple eyes
            ey=ry+self.h//5
            pygame.draw.rect(surf,(200,100,255),(rx+10,ey,8,5))
            pygame.draw.rect(surf,(200,100,255),(rx+self.w-18,ey,8,5))
            alpha_rect(surf,(200,100,255),(rx+8,ey-2,12,9),100)
            alpha_rect(surf,(200,100,255),(rx+self.w-20,ey-2,12,9),100)
            # Orb in hand
            orb_x=rx+(self.w+4 if self.facing_right else -8)
            pygame.draw.circle(surf,(180,80,255),(orb_x,ry+self.h//2),7)
            alpha_rect(surf,(180,80,255),(orb_x-10,ry+self.h//2-10,20,20),50)

        elif self.btype=="dragon":
            bob=int(math.sin(self.anim_tick*0.08)*3)
            # Body
            pygame.draw.ellipse(surf,bc,(rx+4,ry+self.h//3+bob,self.w-8,self.h*2//3))
            # Head
            pygame.draw.ellipse(surf,bc2,(rx+(self.w-30 if self.facing_right else 4),ry+bob,30,self.h//3))
            # Eye
            ex2=rx+(self.w-10 if self.facing_right else 6)
            pygame.draw.circle(surf,(255,220,50),(ex2,ry+self.h//6+bob),5)
            pygame.draw.circle(surf,(255,50,0),(ex2,ry+self.h//6+bob),2)
            # Wings
            wing_y=ry+self.h//4+bob
            wing_flap=int(math.sin(self.anim_tick*0.1)*12)
            pygame.draw.polygon(surf,bc,[(rx+self.w//2,wing_y),(rx-20,wing_y-20-wing_flap),(rx+4,wing_y+12)])
            pygame.draw.polygon(surf,bc,[(rx+self.w//2,wing_y),(rx+self.w+20,wing_y-20-wing_flap),(rx+self.w-4,wing_y+12)])
            # Tail
            pygame.draw.line(surf,bc,(rx+self.w//2,ry+self.h-4+bob),(rx+self.w//2-24,ry+self.h+10+bob),4)
            pygame.draw.line(surf,bc,(rx+self.w//2-24,ry+self.h+10+bob),(rx+self.w//2-12,ry+self.h+20+bob),3)

        # HP bar (wide, at top of boss)
        bar_w=min(self.w*2+40, 200)
        bx=rx+self.w//2-bar_w//2
        pygame.draw.rect(surf,(30,10,10),(bx,ry-18,bar_w,10))
        hp_pct=max(0,self.hp/self.max_hp)
        hp_col=(255,80,80) if hp_pct<0.25 else (255,180,50) if hp_pct<0.5 else (80,220,80)
        pygame.draw.rect(surf,hp_col,(bx,ry-18,int(bar_w*hp_pct),10))
        pygame.draw.rect(surf,(80,40,40),(bx,ry-18,bar_w,10),1)
        name=font_tiny.render(d["name"],True,(220,180,180))
        surf.blit(name,(rx+self.w//2-name.get_width()//2,ry-30))
        p2_lbl=font_tiny.render("PHASE 2" if self.phase==2 else "","True",(255,100,100))
        if self.phase==2: surf.blit(p2_lbl,(rx+self.w//2-p2_lbl.get_width()//2,ry-42))

        # Draw boss projectiles
        for p in self.projectiles:
            px2=int(p["x"]-cx); py2=int(p["y"]-cy)
            pygame.draw.circle(surf,p["color"],(px2,py2),p["w"]//2)
            alpha_rect(surf,p["color"],(px2-p["w"]//2,py2-p["h"]//2,p["w"],p["h"]),40)


# ─────────────────────────────────────────────────────────────────────────────
# Game
# ─────────────────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.bg=Background();self.state="menu"
        # Load persistent high score
        self.high_score=0
        try:
            with open("bhavnobi_score.txt") as f: self.high_score=int(f.read().strip())
        except: pass
        self.shop_ui=ShopUI();self.inv_ui=InvUI();self.trial_ui=TrialUI()
        self.reset()

    def reset(self):
        global theme_idx
        theme_idx=(theme_idx+1)%len(THEMES)
        self.score=0.0;self.combo=1;self.combo_timer=0
        self.cam_x=0.0;self.cam_y=0.0;self.spawn_x=0.0
        self.particles=[];self.ghosts=[];self.shurikens=[]
        self.slash_fxs=[];self.enemies=[];self.platforms=[];self.dmg_nums=[]
        self.bombs=[];self.ground_items=[];self.traders=[];self.trial_pillars=[];self.relic_pillars=[]
        self.boss=None; self.next_boss_score=1000; self.boss_intro=0
        self._ammo_tick=0
        self.placed_blocks=[]      # PlacedBlock list, max 100
        self.build_mode=False      # B key toggles
        self.build_type="stone"    # currently selected block type
        self.build_preview=None    # (gx,gy) of hovered grid cell
        self.shake_t=0;self.shake_mag=0;self.shake_off=(0,0);self.score_flash=0
        self.player=Player(80,HEIGHT*0.45)
        self.shop_ui.close();self.inv_ui.open=False;self.trial_ui.open=False
        self.platforms.append(Platform(-200,int(HEIGHT*0.62),800,"solid"))
        for _ in range(18): self._gen_chunk()

    def _gen_chunk(self):
        gap=random.uniform(75,115);cx=self.spawn_x+gap;last_y=HEIGHT*0.62
        count=random.randint(3,6)
        for _ in range(count):
            pw=random.uniform(60,150);dy=random.uniform(-180,180)*0.88
            ny=max(HEIGHT*0.12,min(HEIGHT*0.74,last_y+dy))
            r=random.random()
            ptype="drop" if r<0.16 else("moving" if r<0.28 else "solid")
            p=Platform(cx,ny,pw,ptype);self.platforms.append(p)
            # Enemy spawn — use spawn_x distance, not score, so all types appear quickly
            dist=self.spawn_x  # how far world has generated
            ec=min(0.60,0.15+dist*0.00004)
            if random.random()<ec and pw>55:
                r2=random.random()
                if   dist>5000 and r2<0.08: et="ninja_e"
                elif dist>4500 and r2<0.16: et="dark_archer"
                elif dist>4000 and r2<0.24: et="knight"
                elif dist>3500 and r2<0.32: et="troll"
                elif dist>3000 and r2<0.40: et="ghost"
                elif dist>2500 and r2<0.50: et="bomber"
                elif dist>1800 and r2<0.58: et="slime"
                elif dist>1200 and r2<0.68: et="jumper"
                elif dist>800  and r2<0.78: et="archer"
                else:                       et="walker"
                e=Enemy(cx+pw/2-9, p.y-28, p, et)
                e.y=p.y-e.h; e.vy=0; e.on_ground=True
                self.enemies.append(e)
            # Ground item spawn (fruits only)
            if ptype=="solid" and random.random()<0.12:
                fruit=random.choice(["apple","berry","mushroom"])
                self.ground_items.append(GroundItem(cx+random.uniform(10,pw-10),ny-20,fruit))
            # Gold coin spawns — common coins, rare piles, very rare chests
            if ptype=="solid" and random.random()<0.25:
                r3=random.random()
                coin_key="gold_chest" if r3<0.05 else "gold_pile" if r3<0.20 else "gold_coin"
                self.ground_items.append(GroundItem(cx+random.uniform(8,max(10,pw-8)),ny-18,coin_key))
            # Trader spawn — every ~400px, high chance on wide platforms
            if ptype=="solid" and pw>70 and random.random()<0.12:
                self.traders.append(Trader(cx+pw/2-10,ny-32,p))
            # Trial pillar — every ~700px, no score gate
            if ptype=="solid" and pw>80 and random.random()<0.08:
                self.trial_pillars.append(TrialPillar(cx+pw/2-11,ny-38,p))
            # Relic trial pillar — rarer, every ~1500px
            if ptype=="solid" and pw>90 and random.random()<0.04:
                self.relic_pillars.append(RelicPillar(cx+pw/2-12,ny-44,p))
            last_y=ny;cx+=pw+gap
        self.spawn_x=cx

    def _shake(self,amt): self.shake_t=int(amt*2);self.shake_mag=amt
    def _ptcl(self,x,y,color,n=8,spd=3.5,life=1.0,size=None):
        for _ in range(n): self.particles.append(Particle(x,y,color,spd,life,size))
    def _blood(self,x,y,n=10): self._ptcl(x,y,(226,75,74),n,4,1.0);self._ptcl(x,y,(180,30,30),n//2,2,0.7)
    def _spark(self,x,y,color=None):
        c=color or(239,159,39); self._ptcl(x,y,c,7,3,0.6);self._ptcl(x,y,(255,220,100),4,5,0.4,size=1.5)
    def _gold_burst(self,x,y,amt):
        for _ in range(min(amt,8)): self._ptcl(x,y,(255,200,30),1,2.5,0.8,size=3)

    def _explode(self,x,y,radius=65):
        self._ptcl(x,y,(255,120,0),20,6,1.2);self._ptcl(x,y,(255,220,50),12,4,0.8)
        self._ptcl(x,y,(80,80,80),10,3,1.5,size=4);self._shake(8)
        n=self.player
        if n.invincible==0 and math.hypot(n.x+n.w/2-x,n.y+n.h/2-y)<radius:
            if n.shield and abs(n.x+n.w/2-x)>30: self._spark(x,y,(100,160,255))
            else: self._hurt_player()
        for i,e in enumerate(self.enemies):
            if not e.dead and math.hypot(e.x+e.w/2-x,e.y+e.h/2-y)<radius:
                self._hit_enemy(i,2,0)

    def _slash(self):
        n=self.player
        if n.slash_cd>0: return
        n.slash_cd=20;n.slash_anim=14
        accent=get_biome(self.cam_x)["accent"];d=1 if n.facing_right else -1
        sx=n.x+(n.w+2 if d>0 else -30);sy=n.y-8;sw=30;sh=n.h+14
        wc=ITEMS.get(n.weapon,{}).get("color",accent)
        self.slash_fxs.append(SlashFX(sx,sy,sw,sh,d,accent,color=wc))
        self._spark(n.x+n.w/2+d*22,n.y+n.h/2,wc)
        hr=pygame.Rect(sx,sy,sw,sh)
        for i,e in enumerate(self.enemies):
            if not e.dead and hr.colliderect(e.rect()): self._hit_enemy(i,n.slash_dmg,d,ax=n.x+n.w/2)
        # Also hit boss
        if self.boss and not self.boss.dead and hr.colliderect(self.boss.rect()):
            if self.boss.invincible==0:
                self.boss.hp-=n.slash_dmg; self.boss.invincible=12
                self._blood(self.boss.x+self.boss.w/2,self.boss.y+self.boss.h//2,6)
                self.dmg_nums.append(DmgNum(self.boss.x+self.boss.w/2,self.boss.y,
                                            str(n.slash_dmg),(239,159,39)))

    def _throw(self):
        n=self.player
        if n.throw_cd>0 or n.ammo<=0: return
        n.throw_cd=16;n.ammo-=1;d=1 if n.facing_right else -1
        self.shurikens.append(Shuriken(n.x+(n.w if d>0 else -12),n.y+n.h/2-5,d*13,-0.8))

    def _hit_enemy(self,idx,dmg,direction=0,ax=None):
        e=self.enemies[idx]
        if e.invincible>0 or e.dead: return
        attacker_x=ax if ax is not None else self.player.x
        n=self.player
        if e.type=="knight" and e.shield_up and e.is_shielded_from(attacker_x):
            self._spark(e.x+e.w/2,e.y+e.h/2,(100,160,255))
            self.dmg_nums.append(DmgNum(e.x+e.w/2,e.y,"BLOCKED",(100,160,255)))
            e.vx+=(direction or 1)*1.5; return
        # Phantom edge — every 5th slash is 3x damage
        actual=max(1,dmg)
        if n.has_relic("phantom_edge"):
            n.slash_count+=1
            if n.slash_count%5==0:
                actual=dmg*3
                self._ptcl(e.x+e.w/2,e.y+e.h/2,(180,100,255),12,4,0.7)
                self.dmg_nums.append(DmgNum(e.x+e.w/2,e.y-8,"PHANTOM!",
                                            RELICS["phantom_edge"]["color"],big=True))
        e.hp-=actual;e.invincible=16
        self._blood(e.x+e.w/2,e.y+e.h/2,10);self._shake(3)
        self.combo+=1;self.combo_timer=140
        if e.hp<=0:
            e.dead=True
            pts=10*self.combo;self.score+=pts;self.score_flash=20
            self.dmg_nums.append(DmgNum(e.x+e.w/2,e.y-16,f"+{pts}",get_biome(self.cam_x)["accent"],big=True))
            self._blood(e.x+e.w/2,e.y+e.h/2,20)
            # Lifesteal relic
            if n.has_relic("bloodstone") and n.hp<n.max_hp:
                n.hp=min(n.max_hp,n.hp+1)
                self.dmg_nums.append(DmgNum(n.x+n.w/2,n.y-10,"+1♥",(80,220,80)))
            # Gold drop
            gold=e.gold_value
            n.gold+=gold
            self._gold_burst(e.x+e.w/2,e.y+e.h/2,gold)
            self.dmg_nums.append(DmgNum(e.x+e.w/2,e.y-30,f"+{gold}g",(255,200,30)))
            # Gear drops
            for drop_key in e.get_drops():
                self.ground_items.append(GroundItem(e.x+e.w/2,e.y,drop_key))
            # Trial kill count
            if self.trial_ui.open: self.trial_ui.killed+=1
        else:
            e.vx+=(direction or 1)*3
            self.dmg_nums.append(DmgNum(e.x+e.w/2,e.y,str(actual),(239,159,39)))

    def _hurt_player(self, raw_dmg=2):
        n=self.player
        if n.invincible>0: return
        # Armor reduces damage — min 1
        dmg=max(1, raw_dmg - int(n.defense))
        n.hp-=dmg
        self.dmg_nums.append(DmgNum(n.x+n.w/2,n.y-10,f"-{dmg}HP",(226,75,74)))
        if n.hp<=0:
            # Soul Lantern — one-time revive
            if n.has_relic("soul_lantern") and not n.revived:
                n.revived=True; n.hp=5; n.invincible=180
                self._ptcl(n.x+n.w/2,n.y+n.h/2,(255,255,150),20,5,1.2)
                self.dmg_nums.append(DmgNum(n.x,n.y-20,"SOUL LANTERN! REVIVED!",(255,255,150),big=True))
                return
            self.high_score=max(self.high_score,int(self.score))
            try:
                with open("bhavnobi_score.txt","w") as f: f.write(str(self.high_score))
            except: pass
            self.state="dead"; return
        n.invincible=110
        self._blood(n.x+n.w/2,n.y+n.h/2,16);self._shake(8)
        if not n.has_relic("warlord"): self.combo=1;self.combo_timer=0
        n.vy=-7

    def update(self,keys,just):
        if self.state!="playing": return
        n=self.player

        # Hotbar 1-5 keys always work (even when UI closed — but not when shop open)
        if not self.shop_ui.open:
            for i in range(5):
                if just.get(getattr(pygame,f"K_{i+1}")):
                    n.use_hotbar(i)

        # Pause physics/gameplay for UIs
        if self.shop_ui.open or self.inv_ui.open: return
        accent=get_biome(self.cam_x)["accent"]
        self.score+=0.05
        if self.spawn_x<self.cam_x+WIDTH+1000: self._gen_chunk()

        # ── Biome ──────────────────────────────────────────────────────────────
        biome=get_biome(self.cam_x)
        self.bg.update(biome, self.cam_x)
        # Track biome transitions
        new_biome_name=biome["name"]
        if not hasattr(self,"_last_biome"): self._last_biome=new_biome_name; self._biome_banner=0
        if new_biome_name!=self._last_biome:
            self._last_biome=new_biome_name; self._biome_banner=180
            self.dmg_nums.append(DmgNum(n.x,n.y-40,
                f"{biome['icon']} Entering {biome['name']}!",biome["accent"],big=True))
        if hasattr(self,"_biome_banner") and self._biome_banner>0: self._biome_banner-=1
        # Space biome: apply lower gravity by modifying vy cap
        space_grav = biome.get("grav",1.0)

        # ── Build mode input ───────────────────────────────────────────────────
        mouse_pos=pygame.mouse.get_pos()
        # Use same integer camera offset as the renderer so preview aligns with placed blocks
        cx_i=int(self.cam_x)+int(self.shake_off[0])
        cy_i=int(self.cam_y)+int(self.shake_off[1])
        world_mx=mouse_pos[0]+cx_i; world_my=mouse_pos[1]+cy_i
        gx=int(world_mx//BLOCK_SIZE); gy=int(world_my//BLOCK_SIZE)
        self.build_preview=(gx,gy) if self.build_mode else None

        if self.build_mode and not self.shop_ui.open and not self.inv_ui.open:
            # Switch block type: Q=stone, W already used, use Tab to cycle
            if just.get(pygame.K_TAB):
                btypes=list(BLOCK_TYPES.keys())
                idx2=btypes.index(self.build_type)
                self.build_type=btypes[(idx2+1)%len(btypes)]

        # Shake
        if self.shake_t>0:
            self.shake_t-=1;m=self.shake_mag*(self.shake_t/max(1,self.shake_mag*2))
            self.shake_off=(random.uniform(-m,m),random.uniform(-m,m))
        else: self.shake_off=(0,0)

        if self.combo_timer>0: self.combo_timer-=1
        else: self.combo=1
        if self.score_flash>0: self.score_flash-=1

        # Cooldowns
        for attr in('slash_cd','slash_anim','dash_cd','throw_cd','invincible','coyote'):
            v=getattr(n,attr)
            if v>0: setattr(n,attr,v-1)
        if n.jump_squat>0: n.jump_squat-=1

        # Shield logic — fixed: hold C drains timer, release starts cooldown
        shield_key=keys[pygame.K_c]
        if n.shield_cd>0:
            n.shield_cd-=1; n.shield=False
        elif shield_key and n.shield_timer<n.SHIELD_MAX:
            n.shield=True; n.shield_timer+=1
            if n.shield_timer>=n.SHIELD_MAX:   # ran out
                n.shield=False; n.shield_cd=n.SHIELD_CD; n.shield_timer=0
        else:
            if n.shield and not shield_key:     # released early — small cooldown
                n.shield_cd=max(30,n.shield_timer//2)
                n.shield_timer=0
            if not shield_key: n.shield=False
            if not shield_key and n.shield_timer>0: n.shield_timer=max(0,n.shield_timer-2)  # regen when not held

        # Player effects tick
        for eff in list(n.effects.keys()):
            n.effects[eff]-=1
            if n.effects[eff]<=0: del n.effects[eff]
        # Regen tick
        if n.regen_timer>0:
            n.regen_timer-=1
            if n.regen_timer%90==0 and n.hp<n.max_hp: n.hp+=1  # +1 HP every 1.5s

        # Weapons
        if just.get(pygame.K_z) or (keys[pygame.K_z] and n.slash_cd==0): self._slash()
        if just.get(pygame.K_x) or (keys[pygame.K_x] and n.throw_cd==0): self._throw()

        # Dash
        if n.dash_timer>0:
            n.dash_timer-=1;n.vx=n.dash_dir*12;n.vy*=0.35
            if n.dash_timer%2==0: self.ghosts.append(Ghost(n.x,n.y,n.w,n.h,accent))
        dk=keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if dk and n.dash_cd==0 and n.dash_timer==0:
            n.dash_timer=9;n.dash_cd=48;n.dash_dir=1 if n.facing_right else -1
            self._ptcl(n.x+n.w/2,n.y+n.h/2,accent,14,5,0.5);self._shake(2)

        # Movement
        left=keys[pygame.K_LEFT] or keys[pygame.K_a]
        right=keys[pygame.K_RIGHT] or keys[pygame.K_d]
        spd=n.move_speed
        if not n.dash_timer:
            if left:  n.vx-=1.5;n.facing_right=False
            if right: n.vx+=1.5;n.facing_right=True
            n.vx*=0.76
            if abs(n.vx)>spd: n.vx=math.copysign(spd,n.vx)
        if n.on_ground and abs(n.vx)>0.5: n.run_tick+=1

        # Jump
        jp=just.get(pygame.K_UP) or just.get(pygame.K_w) or just.get(pygame.K_SPACE)
        if jp:
            if n.on_ground or n.coyote>0:
                n.vy=JUMP_V;n.coyote=0;n.jump_squat=6
                self._ptcl(n.x+n.w/2,n.y+n.h,accent,6,2.5,0.4)
            elif n.on_wall:
                n.vy=JUMP_V*0.9;n.vx=-n.wall_dir*7;n.facing_right=n.wall_dir<0
                self._ptcl(n.x+(0 if n.wall_dir>0 else n.w),n.y+n.h/2,(239,159,39),10,3.5,0.5)

        # Physics
        grav=(GRAVITY if n.vy<0 else GRAVITY_FALL)*space_grav
        n.vy=min(n.vy+grav,20); n.x+=n.vx; n.y+=n.vy
        n.on_ground=False;n.on_wall=False;n.wall_dir=0

        drop=keys[pygame.K_DOWN] or keys[pygame.K_s]
        for p in self.platforms:
            p.update()
            if not n.rect().colliderect(p.rect()): continue
            fT=(n.y+n.h)-p.y;fB=(p.y+p.h)-n.y;fL=(n.x+n.w)-p.x;fR=(p.x+p.w)-n.x
            mn=min(fT,fB,fL,fR)
            if mn==fT and n.vy>=0 and not(p.type=="drop" and drop):
                n.y=p.y-n.h;n.vy=0;n.on_ground=True;n.coyote=8
            elif mn==fB and n.vy<0 and p.type!="drop": n.y=p.y+p.h;n.vy=1
            elif mn==fL and p.type!="drop": n.x=p.x-n.w;n.vx=0;n.on_wall=True;n.wall_dir=1;n.vy=n.vy*0.6 if n.vy>0 else n.vy
            elif mn==fR and p.type!="drop": n.x=p.x+p.w;n.vx=0;n.on_wall=True;n.wall_dir=-1;n.vy=n.vy*0.6 if n.vy>0 else n.vy

        # Camera
        self.cam_x+=(n.x-WIDTH*0.35-self.cam_x)*0.09
        self.cam_y+=(n.y-HEIGHT*0.45-self.cam_y)*0.07

        # ── Placed block collisions ───────────────────────────────────────────
        blocks_to_rm=[]
        for bi,blk in enumerate(self.placed_blocks):
            br=blk.rect()
            # Player collides with block (treat as solid)
            if n.rect().colliderect(br):
                fT=(n.y+n.h)-blk.y; fB=(blk.y+blk.h)-n.y
                fL=(n.x+n.w)-blk.x; fR=(blk.x+blk.w)-n.x
                mn=min(fT,fB,fL,fR)
                bt=blk.btype
                if bt=="spike" and n.invincible==0:
                    self._hurt_player(BLOCK_TYPES["spike"]["dmg"])
                elif bt=="bounce":
                    n.vy=JUMP_V*1.15; n.on_ground=False
                elif mn==fT and n.vy>=0:
                    n.y=blk.y-n.h; n.vy=0; n.on_ground=True; n.coyote=8
                elif mn==fB and n.vy<0: n.y=blk.y+blk.h; n.vy=1
                elif mn==fL: n.x=blk.x-n.w; n.vx=0
                elif mn==fR: n.x=blk.x+blk.w; n.vx=0
            # Enemies hit by spike blocks
            if blk.btype=="spike":
                for j,e in enumerate(self.enemies):
                    if not e.dead and e.rect().colliderect(br):
                        self._hit_enemy(j,BLOCK_TYPES["spike"]["dmg"],0)
                        blk.hp-=1; blk.hit_flash=8
                        if blk.hp<=0: blocks_to_rm.append(bi)
            # Enemies bounce on bounce blocks
            if blk.btype=="bounce":
                for e in self.enemies:
                    if not e.dead and e.vy>0 and e.rect().colliderect(br):
                        e.vy=JUMP_V*0.8
        for bi in sorted(set(blocks_to_rm),reverse=True): self.placed_blocks.pop(bi)

        self.ghosts=[g for g in self.ghosts if g.update()]
        self.slash_fxs=[s for s in self.slash_fxs if s.update()]

        # Shurikens
        to_rm=[]
        for i,s in enumerate(self.shurikens):
            if not s.update(): to_rm.append(i); continue
            removed=False
            for p in self.platforms:
                if s.rect().colliderect(p.rect()):
                    if not s.from_enemy and s.bounces<1: s.vy=-abs(s.vy)*0.5;s.bounces+=1;self._spark(s.x,s.y)
                    else: to_rm.append(i);removed=True
                    break
            if removed: continue
            if not s.from_enemy:
                hit=False
                for j,e in enumerate(self.enemies):
                    if not e.dead and s.rect().colliderect(e.rect()):
                        if e.type=="ghost": continue  # shurikens pass through ghosts
                        self._hit_enemy(j,1,math.copysign(1,s.vx),ax=s.x)
                        self._spark(e.x+e.w/2,e.y+e.h/2,accent); to_rm.append(i);removed=True;hit=True;break
                if not hit and self.boss and not self.boss.dead and self.boss.invincible==0 and s.rect().colliderect(self.boss.rect()):
                    self.boss.hp-=1; self.boss.invincible=6
                    self._spark(s.x,s.y,accent)
                    self.dmg_nums.append(DmgNum(s.x,s.y-8,"1",(239,159,39)))
                    to_rm.append(i);removed=True
            else:
                if n.invincible==0:
                    if n.shield and n.shield_rect().colliderect(s.rect()):
                        self._spark(s.x,s.y,(100,160,255));to_rm.append(i);removed=True
                    elif s.rect().colliderect(n.rect()):
                        self._hurt_player(2);to_rm.append(i);removed=True
            if not removed and(s.x<self.cam_x-300 or s.x>self.cam_x+WIDTH+300 or s.y>DEATH_Y+200): to_rm.append(i)
        for i in sorted(set(to_rm),reverse=True):
            if i<len(self.shurikens): self.shurikens.pop(i)

        # Enemies
        to_rm=[]
        to_spawn=[]   # new enemies to add after loop (slime splits)
        for i,e in enumerate(self.enemies):
            if not e.update(self.platforms): to_rm.append(i); continue
            if e.dead: continue
            if e.type in("jumper","bomber","knight","troll","ninja_e","dark_archer","ghost"):
                e.facing_right=n.x>e.x
            # Archer — straight shuriken
            if e.type=="archer" and e.shoot_cd<=0:
                e.shoot_cd=180;d2=1 if n.x>e.x else -1
                self.shurikens.append(Shuriken(e.x+e.w/2,e.y+e.h/2,d2*7,-2,from_enemy=True))
            # Dark archer — homing arrow (shuriken that curves toward player)
            if e.type=="dark_archer" and e.shoot_cd<=0:
                e.shoot_cd=140
                dx=n.x-(e.x+e.w/2); dy=n.y-(e.y+e.h/2)
                dist=max(1,math.hypot(dx,dy))
                s=Shuriken(e.x+e.w/2,e.y+e.h/2,dx/dist*6,dy/dist*6-2,from_enemy=True)
                s.homing=True; s.homing_target=(n,)  # weak ref via tuple
                self.shurikens.append(s)
            if e.shoot_cd>0: e.shoot_cd-=1
            # Bomber
            if e.type=="bomber" and e.bomb_cd<=0 and e.on_ground:
                e.bomb_cd=random.randint(150,260);e.bomb_warn=0
                dx=n.x-(e.x+e.w/2);dy=n.y-(e.y+e.h/2);dist=max(1,math.hypot(dx,dy))
                self.bombs.append(Bomb(e.x+e.w/2,e.y,dx/dist*6,min(-4,dy/dist*6-3)))
            # Knight charge
            if e.type=="knight": e.vx=math.copysign(1.8,n.x-e.x) if abs(n.x-e.x)<220 else e.vx*0.9
            # Jumper homing
            if e.type=="jumper" and e.jump_warn: e.vx=math.copysign(3,n.x-e.x)
            # Troll — slow walk + charge when close
            if e.type=="troll":
                dist_t=abs(n.x-e.x)
                if dist_t<200 and e.charge_cd==0 and e.on_ground:
                    e.charging=True; e.vx=math.copysign(3.5,n.x-e.x); e.charge_cd=120
                elif e.charge_cd>90: pass  # still charging
                else: e.charging=False; e.vx=math.copysign(0.6,n.x-e.x)
            # Ninja enemy — dashes at player
            if e.type=="ninja_e":
                e.vx=math.copysign(2.5,n.x-e.x)
                if e.dash_cd==0 and abs(n.x-e.x)<250 and e.on_ground:
                    e.dash_timer=8; e.dash_cd=80
                    e.vx=math.copysign(10,n.x-e.x)
                if e.dash_timer>0: e.vx=math.copysign(10,n.x-e.x)
            # Collision with player
            if n.invincible==0 and "invis" not in n.effects and n.rect().colliderect(e.rect()):
                # Ghost — can't stomp, always hurts
                if e.type=="ghost":
                    self._hurt_player(ENEMY_DMG.get(e.type,2))
                elif n.vy>0 and n.y+n.h<e.y+e.h*0.4:
                    self._hit_enemy(i,99,0,ax=n.x+n.w/2)
                    if n.has_relic("stomp_boots"):
                        n.vy=JUMP_V*1.1
                        for j,e2 in enumerate(self.enemies):
                            if j!=i and not e2.dead and math.hypot(e2.x-e.x,e2.y-e.y)<80:
                                self._hit_enemy(j,3,0)
                        self._ptcl(e.x+e.w/2,e.y,(200,140,60),10,4,0.6)
                    else:
                        n.vy=JUMP_V*0.7
                        # Troll takes double from stomp even without relic
                        if e.type=="troll": self._hit_enemy(i,3,0)
                elif n.shield and n.shield_rect().colliderect(e.rect()):
                    self._spark(e.x+e.w/2,e.y+e.h/2,(100,160,255))
                    e.vx=math.copysign(4,e.x-n.x); e.invincible=20
                else:
                    dmg=ENEMY_DMG.get(e.type,2)
                    if e.type=="troll" and getattr(e,"charging",False): dmg=6
                    self._hurt_player(dmg)
            # Slime split on death
            if e.dead and not getattr(e,"is_mini",False) and not getattr(e,"_split",False):
                e._split=True
                for _ in range(2):
                    mini=Enemy(e.x+random.randint(-10,10),e.y,"slime",e.plat)
                    mini.hp=1;mini.max_hp=1;mini.w=12;mini.h=12
                    mini.is_mini=True;mini.gold_value=3
                    to_spawn.append(mini)
        for i in sorted(set(to_rm),reverse=True): self.enemies.pop(i)
        self.enemies.extend(to_spawn)

        # Bombs
        to_rm2=[]
        for i,b in enumerate(self.bombs):
            if not b.update(): to_rm2.append(i); continue
            for p in self.platforms:
                if b.rect().colliderect(p.rect()):
                    if b.bounces<2: b.vy=-abs(b.vy)*0.6;b.bounces+=1;b.vx*=0.8
                    else: b.fuse=0
                    break
            if b.fuse<=0: self._explode(b.x,b.y); to_rm2.append(i)
        for i in sorted(set(to_rm2),reverse=True):
            if i<len(self.bombs): self.bombs.pop(i)

        # Ground item pickup
        to_rm3=[]
        for i,gi in enumerate(self.ground_items):
            gi.update(self.platforms)
            if n.rect().inflate(8,8).colliderect(gi.rect()):
                data=ITEMS.get(gi.key,{})
                if data.get("cat")=="gold":
                    amt=data.get("gold",5)
                    n.gold+=amt
                    n.last_pickup_msg=f"+{amt} Gold!"; n.last_pickup_timer=80
                    self._gold_burst(gi.x,gi.y,amt)
                else:
                    n.add_item(gi.key)
                    self.dmg_nums.append(DmgNum(gi.x,gi.y,ITEMS[gi.key]["name"],(180,220,120)))
                to_rm3.append(i)
        for i in sorted(set(to_rm3),reverse=True): self.ground_items.pop(i)

        # Traders — check proximity
        for t2 in self.traders:
            t2.update(); dist=abs(n.x-t2.x)
            t2.active=dist<80
            if t2.active and just.get(pygame.K_e): self.shop_ui.show(t2)

        # Trial pillars — check proximity
        for tp in self.trial_pillars:
            tp.update(); dist=abs(n.x-tp.x)
            tp.active=dist<90 and not tp.completed
            if tp.active and just.get(pygame.K_e) and not self.trial_ui.open:
                self.trial_ui.start(tp)
                # Spawn trial enemies right near the pillar so player can find them
                for ei in range(self.trial_ui.enemies_to_kill+1):
                    offset=random.choice([-1,1])*(80+ei*60)
                    # Find a nearby platform to stand on
                    plat=tp.plat if tp.plat else (self.platforms[0] if self.platforms else None)
                    if plat:
                        ex=tp.x+offset
                        te=Enemy(ex, plat.y-28, plat, "walker")
                        te.y=plat.y-te.h; te.vy=0; te.on_ground=True
                        self.enemies.append(te)
        # Relic pillars
        for rp in self.relic_pillars:
            rp.update(); dist=abs(n.x-rp.x)
            rp.active=dist<90 and not rp.completed
            if rp.active and just.get(pygame.K_e) and not self.trial_ui.open:
                # Start a harder relic trial
                self.trial_ui.open=True
                self.trial_ui.pillar=rp
                self.trial_ui.killed=0
                self.trial_ui.enemies_to_kill=random.randint(6,10)
                self.trial_ui.timer=3000   # 50s
                self.trial_ui.is_relic=True
                # Spawn mixed harder enemies near pillar
                etypes=["walker","archer","jumper","walker","archer"]
                for ei,et in enumerate(etypes[:self.trial_ui.enemies_to_kill]):
                    offset=random.choice([-1,1])*(70+ei*55)
                    plat=rp.plat or (self.platforms[0] if self.platforms else None)
                    if plat:
                        te=Enemy(rp.x+offset, plat.y-28, plat, et)
                        te.y=plat.y-te.h; te.vy=0; te.on_ground=True
                        self.enemies.append(te)

        # Trial logic
        if self.trial_ui.open:
            self.trial_ui.timer-=1
            is_relic=getattr(self.trial_ui,"is_relic",False)
            if self.trial_ui.killed>=self.trial_ui.enemies_to_kill or self.trial_ui.timer<=0:
                if self.trial_ui.killed>=self.trial_ui.enemies_to_kill:
                    pillar=self.trial_ui.pillar; pillar.completed=True
                    gold_bonus=30+random.randint(10,20)
                    n.gold+=gold_bonus
                    if is_relic:
                        rkey=pillar.reward
                        if n.equip_relic(rkey):
                            self.dmg_nums.append(DmgNum(n.x,n.y-20,
                                f"★ RELIC: {RELICS[rkey]['name']}!",RELICS[rkey]["color"],big=True))
                        else:
                            self.dmg_nums.append(DmgNum(n.x,n.y-20,
                                "Relic slots full! (max 3)",(200,150,100),big=True))
                    else:
                        n.add_item(pillar.reward)
                        self.dmg_nums.append(DmgNum(n.x,n.y-20,
                            f"TRIAL COMPLETE! +{ITEMS[pillar.reward]['name']} +{gold_bonus}g",
                            (200,150,255),big=True))
                else:
                    self.dmg_nums.append(DmgNum(n.x,n.y-20,"TRIAL FAILED — time up!",(226,75,74),big=True))
                self.trial_ui.open=False
                self.trial_ui.is_relic=False

        # ── Passive relic effects ─────────────────────────────────────────────
        ticks=pygame.time.get_ticks()
        # Gold magnet — auto-collect coins within 100px
        if n.has_relic("gold_magnet"):
            to_rm_mag=[]
            for i,gi in enumerate(self.ground_items):
                if ITEMS.get(gi.key,{}).get("cat")=="gold":
                    if math.hypot(n.x-gi.x, n.y-gi.y)<100:
                        amt=ITEMS[gi.key].get("gold",5)
                        n.gold+=amt; self._gold_burst(gi.x,gi.y,amt)
                        to_rm_mag.append(i)
            for i in sorted(set(to_rm_mag),reverse=True): self.ground_items.pop(i)
        # Dash stone — fire trail during dash
        if n.has_relic("dash_stone") and n.dash_timer>0 and n.dash_timer%3==0:
            self._ptcl(n.x+n.w/2,n.y+n.h/2,(255,120,0),4,3,0.4)
        # Void step — damage enemies during dash
        if n.has_relic("void_step") and n.dash_timer>0:
            for i,e in enumerate(self.enemies):
                if not e.dead and e not in n.void_step_hit and n.rect().colliderect(e.rect()):
                    self._hit_enemy(i,2,n.dash_dir)
                    n.void_step_hit.add(e)
        if n.dash_timer==0: n.void_step_hit=set()
        # Gravity gem — slow fall when holding jump
        if n.has_relic("gravity") and not n.on_ground:
            jp_held=keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
            if jp_held and n.vy>0: n.vy=min(n.vy,2.5)
        # Shield rune — halve shield cooldown
        if n.has_relic("shield_rune") and n.shield_cd>0 and ticks%2==0:
            n.shield_cd=max(0,n.shield_cd-1)  # drain cd twice as fast
        # Dash stone — halve dash cooldown
        if n.has_relic("dash_stone") and n.dash_cd>0 and ticks%2==0:
            n.dash_cd=max(0,n.dash_cd-1)
        # Warlord crown — combo never resets on hit
        # (handled by not resetting in _hurt_player when relic present)
        # Last stand glow
        if n.has_relic("last_stand") and n.hp<=3:
            alpha_rect(screen,(255,50,50),(0,0,WIDTH,HEIGHT),int(15+10*math.sin(ticks*0.008)))

        # ── Boss spawning at 1000-point milestones ────────────────────────────
        if self.score>=self.next_boss_score and self.boss is None:
            self.boss_intro=180  # 3s intro
            # Pick boss type by milestone
            if self.next_boss_score<=1000:   btype="golem"
            elif self.next_boss_score<=2000: btype="shadow"
            else:                             btype="dragon"
            # Spawn on a platform near the player
            spawn_plat=None
            for p in self.platforms:
                if abs(p.x-n.x-400)<300 and p.type=="solid":
                    spawn_plat=p; break
            if spawn_plat is None and self.platforms:
                spawn_plat=self.platforms[-1]
            if spawn_plat:
                bd=BOSS_DATA[btype]
                bx=spawn_plat.x+spawn_plat.w//2-bd["w"]//2
                by=spawn_plat.y-bd["h"]
                self.boss=Boss(bx,by,btype,spawn_plat)
                self.boss_intro=180
                self.next_boss_score+=1000

        # ── Boss update ───────────────────────────────────────────────────────
        if self.boss:
            if self.boss_intro>0: self.boss_intro-=1
            alive=self.boss.update(self.platforms, n)
            if not alive:
                # Boss died — drop legendary loot + gold
                bd=BOSS_DATA[self.boss.btype]
                n.gold+=bd["gold"]
                self._gold_burst(self.boss.x+self.boss.w/2, self.boss.y, bd["gold"])
                self.dmg_nums.append(DmgNum(self.boss.x+self.boss.w/2,self.boss.y-20,
                    f"BOSS DEFEATED! +{bd['gold']}g",(255,200,50),big=True))
                # Drop tier-appropriate weapon or armor
                drops={"golem":["gold_sword","plate","chainmail"],
                       "shadow":["shadow_blade","void_armor","obsidian_edge"],
                       "dragon":["cosmic_blade","dragon_scale","dragon_fang"]}
                drop=random.choice(drops[self.boss.btype])
                self.ground_items.append(GroundItem(self.boss.x+self.boss.w/2,self.boss.y,drop))
                self.score+=500
                self.boss=None
            else:
                # Boss projectile hits
                for p in self.boss.projectiles:
                    pr=pygame.Rect(p["x"]-p["w"]//2,p["y"]-p["h"]//2,p["w"],p["h"])
                    if n.invincible==0:
                        if n.shield and n.shield_rect().colliderect(pr):
                            p["life"]=-1; self._spark(p["x"],p["y"],(100,160,255))
                        elif pr.colliderect(n.rect()):
                            self._hurt_player(p["dmg"]); p["life"]=-1
                # Boss melee hit
                if n.invincible==0 and n.rect().colliderect(self.boss.rect()):
                    if n.vy>0 and n.y+n.h<self.boss.y+self.boss.h*0.3:
                        # Stomp — damage boss
                        dmg=n.slash_dmg*2
                        self.boss.hp-=dmg; self.boss.invincible=20
                        self._blood(self.boss.x+self.boss.w/2,self.boss.y+self.boss.h//2,8)
                        self.dmg_nums.append(DmgNum(self.boss.x+self.boss.w/2,self.boss.y,str(dmg),(239,159,39)))
                        n.vy=JUMP_V*0.8
                        if n.has_relic("bloodstone"): n.hp=min(n.max_hp,n.hp+1)
                    elif not(n.shield and n.shield_rect().colliderect(self.boss.rect())):
                        self._hurt_player(4)

        # Ammo regen — use frame tick, not score modulo (avoids spam at score==0)
        if not hasattr(self,'_ammo_tick'): self._ammo_tick=0
        self._ammo_tick+=1
        regen_rate=90 if n.has_relic("quiver") else 180  # frames between regen (+2 ammo)
        if self._ammo_tick%regen_rate==0 and n.ammo<n.max_ammo:
            n.ammo=min(n.max_ammo, n.ammo+2)

        # Cull
        self.particles=[p for p in self.particles if p.update()]
        self.dmg_nums=[d for d in self.dmg_nums if d.update()]
        self.platforms=[p for p in self.platforms if p.x+p.w>self.cam_x-400]
        self.enemies=[e for e in self.enemies if e.x>self.cam_x-400 and e.y<DEATH_Y+300]
        self.ground_items=[g for g in self.ground_items if g.x>self.cam_x-400]
        self.traders=[t2 for t2 in self.traders if t2.x>self.cam_x-400]
        self.trial_pillars=[tp for tp in self.trial_pillars if tp.x>self.cam_x-400]
        self.relic_pillars=[rp for rp in self.relic_pillars if rp.x>self.cam_x-400]

        # Death
        if n.y>DEATH_Y and self.state=="playing":
            self.high_score=max(self.high_score,int(self.score))
            try:
                with open("bhavnobi_score.txt","w") as f: f.write(str(self.high_score))
            except: pass
            n.hp=0; self.state="dead"

    def draw(self):
        biome=get_biome(self.cam_x)
        plat_top=biome["plat_top"]; plat_shd=biome["plat_shd"]; accent=biome["accent"]
        sx,sy=int(self.shake_off[0]),int(self.shake_off[1])
        cx=int(self.cam_x)+sx;cy=int(self.cam_y)+sy
        self.bg.draw(screen,self.cam_x,self.cam_y,biome)
        for g in self.ghosts:          g.draw(screen,cx,cy)
        # Draw placed blocks
        for blk in self.placed_blocks: blk.draw(screen,cx,cy)
        # Build preview (ghost block at cursor)
        if self.build_mode and self.build_preview:
            pgx,pgy=self.build_preview
            prx=pgx*BLOCK_SIZE-cx; pry=pgy*BLOCK_SIZE-cy
            d=BLOCK_TYPES[self.build_type]
            # Check if there's an existing block at hover — show red delete highlight
            hover_block=next((b for b in self.placed_blocks if b.gx==pgx and b.gy==pgy),None)
            if hover_block:
                # Red overlay on existing block + D hint
                alpha_rect(screen,(220,50,50),(prx,pry,BLOCK_SIZE,BLOCK_SIZE),80)
                pygame.draw.rect(screen,(255,80,80),(prx,pry,BLOCK_SIZE,BLOCK_SIZE),2)
                dl=font_tiny.render("D=break",True,(255,100,100))
                screen.blit(dl,(prx+BLOCK_SIZE//2-dl.get_width()//2,pry-14))
            else:
                # Ghost preview for placing
                can=self.player.gold>=d["cost"] and len(self.placed_blocks)<100
                alpha_rect(screen,d["color"] if can else (100,60,60),(prx,pry,BLOCK_SIZE,BLOCK_SIZE),80)
                pygame.draw.rect(screen,d["color"] if can else (150,80,80),(prx,pry,BLOCK_SIZE,BLOCK_SIZE),2)
        for p in self.platforms:       p.draw(screen,cx,cy,accent,plat_top,plat_shd)
        for gi in self.ground_items:   gi.draw(screen,cx,cy)
        for t2 in self.traders:        t2.draw(screen,cx,cy)
        for tp in self.trial_pillars:  tp.draw(screen,cx,cy)
        for rp in self.relic_pillars:  rp.draw(screen,cx,cy)
        for s in self.slash_fxs:       s.draw(screen,cx,cy)
        for s in self.shurikens:       s.draw(screen,cx,cy,(226,75,74) if s.from_enemy else accent)
        for e in self.enemies:         e.draw(screen,cx,cy,accent)
        for b in self.bombs:           b.draw(screen,cx,cy)
        if self.boss:                  self.boss.draw(screen,cx,cy,accent)
        for p in self.particles:       p.draw(screen,cx,cy)
        for d in self.dmg_nums:        d.draw(screen,cx,cy)
        self.player.draw(screen,cx,cy,accent)
        # Vignette
        for i in range(5):
            alpha_rect(screen,(0,0,0),(0,0,10-i*2,HEIGHT),55-i*9)
            alpha_rect(screen,(0,0,0),(WIDTH-10+i*2,0,10-i*2,HEIGHT),55-i*9)
        # Boss intro banner
        if self.boss and self.boss_intro>0:
            t=min(1.0,self.boss_intro/60)
            bd=BOSS_DATA[self.boss.btype]
            alpha_rect(screen,(0,0,0),(0,HEIGHT//2-50,WIDTH,100),int(t*200))
            bi=font_big.render(f"⚠  {bd['name'].upper()}  ⚠",True,bd["col2"])
            bi.set_alpha(int(t*255)); screen.blit(bi,(WIDTH//2-bi.get_width()//2,HEIGHT//2-36))
            bd2=font_med.render(bd["desc"],True,(200,160,120))
            bd2.set_alpha(int(t*200)); screen.blit(bd2,(WIDTH//2-bd2.get_width()//2,HEIGHT//2+4))
        # Biome transition banner
        if hasattr(self,"_biome_banner") and self._biome_banner>0:
            t2=min(1.0,self._biome_banner/30)
            bm=get_biome(self.cam_x)
            alpha_rect(screen,(0,0,0),(0,HEIGHT//2-28,WIDTH,56),int(t2*160))
            btxt=font_big.render(f"{bm['icon']}  {bm['name'].upper()}  {bm['icon']}",True,bm["accent"])
            btxt.set_alpha(int(t2*255))
            screen.blit(btxt,(WIDTH//2-btxt.get_width()//2,HEIGHT//2-22))
        self._hud(accent)
        self.trial_ui.draw(screen)
        self.shop_ui.draw(screen,self.player)
        self.inv_ui.draw(screen,self.player)

    def _hud(self,accent):
        n=self.player;ticks=pygame.time.get_ticks()
        scol=accent if self.score_flash>0 else (200,200,200)
        # Score
        screen.blit(font_tiny.render("SCORE",True,(70,70,70)),(18,14))
        screen.blit(font_big.render(f"{int(self.score):06d}",True,scol),(18,26))
        spd=min(1.0,self.score/3000)
        screen.blit(font_tiny.render(f"SPEED {'█'*int(spd*8)}{'░'*(8-int(spd*8))}",True,(55,55,55)),(18,66))
        if self.combo_timer>0 and self.combo>1:
            screen.blit(font_med.render(f"x{self.combo} COMBO",True,(239,159,39)),(18,82))
        # HP bar (scales to max_hp=10)
        screen.blit(font_tiny.render("HP",True,(70,70,70)),(WIDTH-160,14))
        bar_w=140; bar_h=14
        pygame.draw.rect(screen,(30,10,10),(WIDTH-160,26,bar_w,bar_h))
        hp_fill=int(bar_w*max(0,n.hp)/n.max_hp)
        hp_col=(80,220,80) if n.hp>n.max_hp*0.6 else (220,180,40) if n.hp>n.max_hp*0.3 else (220,60,60)
        pygame.draw.rect(screen,hp_col,(WIDTH-160,26,hp_fill,bar_h))
        pygame.draw.rect(screen,(60,40,40),(WIDTH-160,26,bar_w,bar_h),1)
        hp_txt=font_tiny.render(f"{n.hp}/{n.max_hp}",True,(200,200,200))
        screen.blit(hp_txt,(WIDTH-160+bar_w//2-hp_txt.get_width()//2,27))
        # Gold
        gc=font_med.render(f"⬡{n.gold}",True,(255,200,30)); screen.blit(gc,(WIDTH-160,46))
        # Ammo
        screen.blit(font_tiny.render("THROW",True,(70,70,70)),(WIDTH-160,68))
        for i in range(8):
            col=accent if i<n.ammo else (35,35,35)
            pts=self._star(WIDTH-157+(i*14),82,5); pygame.draw.polygon(screen,col,pts)
        # Equipment indicator
        wn=ITEMS.get(n.weapon,{}).get("name","?"); an=ITEMS.get(n.armor,{}).get("name","?")
        wc2=ITEMS.get(n.weapon,{}).get("color",(160,160,160)); ac2=ITEMS.get(n.armor,{}).get("color",(160,140,120))
        screen.blit(font_tiny.render(f"⚔ {wn}",True,wc2),(WIDTH-160,96))
        screen.blit(font_tiny.render(f"🛡 {an}",True,ac2),(WIDTH-160,110))
        # Active effects
        ey=124
        for eff,frames in n.effects.items():
            ec2=(80,200,255) if eff=="speed" else (255,80,0) if eff=="power" else (100,160,255) if eff=="barrier" else (180,120,255) if eff=="invis" else (80,220,120)
            screen.blit(font_tiny.render(f"{eff.upper()} {frames//60}s",True,ec2),(WIDTH-160,ey)); ey+=14
        # Relic gem icons
        if n.relics:
            screen.blit(font_tiny.render("RELICS",True,(80,140,200)),(18,HEIGHT-88))
            for ri,rkey in enumerate(n.relics):
                rd=RELICS[rkey]; gc=rd["gem"]
                gx=18+ri*56; gy=HEIGHT-72
                # Diamond gem shape
                pygame.draw.polygon(screen,gc,[(gx+12,gy),(gx+22,gy+10),(gx+12,gy+20),(gx+2,gy+10)])
                pygame.draw.polygon(screen,(min(255,gc[0]+80),min(255,gc[1]+80),min(255,gc[2]+80)),
                                    [(gx+12,gy),(gx+22,gy+10),(gx+12,gy+10),(gx+2,gy+10)])
                pygame.draw.polygon(screen,(20,10,40),[(gx+12,gy),(gx+22,gy+10),(gx+12,gy+20),(gx+2,gy+10)],1)
                # Relic name below
                rl=font_tiny.render(rd["name"][:8],True,rd["color"])
                screen.blit(rl,(gx+12-rl.get_width()//2,gy+22))
        # Empty relic slots
        for ri in range(3):
            if ri>=len(n.relics):
                gx=18+ri*56; gy=HEIGHT-72
                pygame.draw.polygon(screen,(25,20,40),[(gx+12,gy),(gx+22,gy+10),(gx+12,gy+20),(gx+2,gy+10)],1)
                el=font_tiny.render("empty",True,(30,25,50)); screen.blit(el,(gx+12-el.get_width()//2,gy+22))
        # Dash bar
        pygame.draw.rect(screen,(18,18,18),(18,HEIGHT-26,100,8))
        fill=int(100*(1-n.dash_cd/48)) if n.dash_cd>0 else 100
        pygame.draw.rect(screen,accent,(18,HEIGHT-26,fill,8))
        alpha_rect(screen,accent,(18,HEIGHT-26,fill,8),38)
        screen.blit(font_tiny.render("DASH",True,(55,55,55)),(22,HEIGHT-40))
        # Shield bar
        pygame.draw.rect(screen,(18,18,18),(130,HEIGHT-26,100,8))
        if n.shield_cd>0:
            sf=int(100*(1-n.shield_cd/n.SHIELD_CD)); pygame.draw.rect(screen,(60,100,160),(130,HEIGHT-26,sf,8))
            screen.blit(font_tiny.render("SHIELD CD",True,(55,55,55)),(134,HEIGHT-40))
        else:
            sf2=int(100*(1-n.shield_timer/n.SHIELD_MAX)) if n.shield_timer>0 else 100
            pygame.draw.rect(screen,(100,160,255),(130,HEIGHT-26,sf2,8))
            alpha_rect(screen,(100,160,255),(130,HEIGHT-26,sf2,8),40)
            lbl="SHIELDING" if n.shield else "SHIELD [C]"
            screen.blit(font_tiny.render(lbl,True,(100,160,255) if n.shield else (55,55,55)),(134,HEIGHT-40))
        # Hotbar
        for i,slot in enumerate(n.hotbar):
            hx=WIDTH//2-120+i*52; hy=HEIGHT-42
            sel=i==n.selected_slot
            pygame.draw.rect(screen,(15,20,35),(hx,hy,44,36))
            pygame.draw.rect(screen,(255,220,80) if sel else (40,60,100),(hx,hy,44,36),2 if sel else 1)
            screen.blit(font_tiny.render(str(i+1),True,(80,80,120)),(hx+3,hy+2))
            if slot and slot in ITEMS:
                v2=ITEMS[slot]; pygame.draw.rect(screen,v2["color"],(hx+14,hy+8,18,18))
                cnt2=n.inventory.get(slot,0)
                screen.blit(font_tiny.render(str(cnt2),True,(200,200,100)),(hx+34,hy+2))
        # Biome indicator — top centre
        biome=get_biome(self.cam_x)
        bi_text=font_tiny.render(f"{biome['icon']} {biome['name']}",True,biome["accent"])
        screen.blit(bi_text,(WIDTH//2-bi_text.get_width()//2,4))
        # Controls hint (update to include B=build)
        ctrl="WASD·SHIFT=Dash·Z=Slash·X=Throw·C=Shield·E=Interact·I=Inv·1-5=Use·B=Build"
        screen.blit(font_tiny.render(ctrl,True,(30,30,30)),(WIDTH//2-290,HEIGHT-14))
        # Best score
        if self.high_score>0:
            screen.blit(font_tiny.render(f"BEST {self.high_score:06d}",True,(50,50,50)),(WIDTH//2-40,14))
        # Pickup message
        if n.last_pickup_timer>0:
            n.last_pickup_timer-=1
            alpha=min(255,n.last_pickup_timer*4)
            pm=font_small.render(n.last_pickup_msg,True,(180,220,120)); pm.set_alpha(alpha)
            screen.blit(pm,(WIDTH//2-pm.get_width()//2,HEIGHT//2-80))
        # Build mode HUD panel
        if self.build_mode:
            bx=WIDTH//2-180; by=HEIGHT-68
            pygame.draw.rect(screen,(10,15,25),(bx,by,360,52))
            pygame.draw.rect(screen,(60,180,255),(bx,by,360,52),1)
            screen.blit(font_small.render("BUILD MODE  [B]=Exit  [Tab]=Cycle  LClick=Place  RClick/D=Break",
                                          True,(80,200,255)),(bx+8,by+4))
            for ti,tname in enumerate(BLOCK_TYPES.keys()):
                td=BLOCK_TYPES[tname]; tx=bx+12+ti*116; ty=by+22
                sel=tname==self.build_type
                pygame.draw.rect(screen,(30,40,60) if sel else (15,20,35),(tx,ty,108,24))
                pygame.draw.rect(screen,td["color"],(tx,ty,108,24),2 if sel else 1)
                pygame.draw.rect(screen,td["color"],(tx+4,ty+4,16,16))
                can=n.gold>=td["cost"]
                cost_col=(100,255,100) if can else (200,80,80)
                lbl=font_tiny.render(f"{td['name']} {td['cost']}g",True,
                                     (255,240,100) if sel else (150,160,170))
                screen.blit(lbl,(tx+24,ty+6))
            # Block count
            cnt_col=(80,200,80) if len(self.placed_blocks)<80 else (255,140,0) if len(self.placed_blocks)<100 else (220,60,60)
            screen.blit(font_tiny.render(f"{len(self.placed_blocks)}/100 blocks",True,cnt_col),(bx+300,by+36))

        # Minimap
        self._minimap(accent)

    def _minimap(self, accent):
        """Shows ~2500px of world ahead as a strip. Icons for key objects."""
        n=self.player
        # Minimap dimensions and position — bottom right above shield bar
        MW=260; MH=52; MX=WIDTH-MW-14; MY=HEIGHT-MH-60
        LOOK=2500  # how many world-px ahead to show
        # Background
        pygame.draw.rect(screen,(8,10,18),(MX,MY,MW,MH))
        pygame.draw.rect(screen,(35,40,55),(MX,MY,MW,MH),1)
        alpha_rect(screen,(0,0,10),(MX,MY,MW,MH),120)
        # Label
        screen.blit(font_tiny.render("MAP",True,(50,55,70)),(MX+4,MY+2))
        # Player marker (white triangle at left edge)
        px2=MX+8
        pygame.draw.polygon(screen,(255,255,255),[(px2-4,MY+MH//2+6),(px2+4,MY+MH//2+6),(px2,MY+MH//2-2)])
        # World range shown
        cam=self.cam_x
        def world_to_map(wx):
            """Convert world x to minimap screen x"""
            return int(MX+8+((wx-cam)/LOOK)*(MW-16))
        # Biome colour bands
        biome_start=int(cam//BIOME_LEN)*BIOME_LEN
        for bi_off in range(0, LOOK+BIOME_LEN, BIOME_LEN):
            bx_world=biome_start+bi_off
            bx_screen=world_to_map(bx_world)
            bx_end=world_to_map(bx_world+BIOME_LEN)
            bx_screen=max(MX+8,bx_screen); bx_end=min(MX+MW-8,bx_end)
            if bx_end<=MX+8: continue
            b=get_biome_at(bx_world+BIOME_LEN//2)
            col=b["accent"]
            alpha_rect(screen,col,(bx_screen,MY+2,max(1,bx_end-bx_screen),MH-4),18)
            # Biome icon at transition
            if bx_screen>MX+16:
                icon=font_tiny.render(b["icon"],True,(*col[:3],))
                screen.blit(icon,(bx_screen-6,MY+2))
        # Platforms as grey blocks
        for p in self.platforms:
            if p.x<cam or p.x>cam+LOOK: continue
            px3=world_to_map(p.x); pw3=max(3,int(p.w/LOOK*(MW-16)))
            py3=MY+int((p.y/HEIGHT)*MH*0.7)
            py3=max(MY+4,min(MY+MH-8,py3))
            pygame.draw.rect(screen,(60,65,75),(px3,py3,pw3,3))
        # Traders — gold ⬡ icon
        for t2 in self.traders:
            if cam<t2.x<cam+LOOK:
                tx3=world_to_map(t2.x)
                pygame.draw.circle(screen,(255,200,30),(tx3,MY+MH//2-4),5)
                pygame.draw.circle(screen,(200,140,10),(tx3,MY+MH//2-4),5,1)
                screen.blit(font_tiny.render("T",True,(255,230,80)),(tx3-3,MY+MH//2-7))
        # Trial pillars — purple ◆
        for tp in self.trial_pillars:
            if cam<tp.x<cam+LOOK and not tp.completed:
                tx3=world_to_map(tp.x)
                pygame.draw.polygon(screen,(160,80,255),
                    [(tx3,MY+6),(tx3+5,MY+MH//2-2),(tx3,MY+MH-8),(tx3-5,MY+MH//2-2)])
                screen.blit(font_tiny.render("!",True,(200,150,255)),(tx3-2,MY+MH//2-7))
        # Relic pillars — blue ◆
        for rp in self.relic_pillars:
            if cam<rp.x<cam+LOOK and not rp.completed:
                tx3=world_to_map(rp.x)
                pygame.draw.polygon(screen,(60,160,255),
                    [(tx3,MY+4),(tx3+6,MY+MH//2-2),(tx3,MY+MH-6),(tx3-6,MY+MH//2-2)])
                screen.blit(font_tiny.render("R",True,(100,200,255)),(tx3-3,MY+MH//2-8))
        # Boss marker — red skull-ish ✦
        if self.boss and cam<self.boss.x<cam+LOOK:
            bx3=world_to_map(self.boss.x)
            pygame.draw.rect(screen,(220,50,50),(bx3-5,MY+4,10,MH-8))
            screen.blit(font_tiny.render("B",True,(255,80,80)),(bx3-3,MY+MH//2-8))
        # Boss skull at next_boss_score distance estimate
        elif not self.boss:
            score_dist=(self.next_boss_score-self.score)*2  # rough px estimate
            if 0<score_dist<LOOK:
                bx3=world_to_map(cam+score_dist)
                pulse=int(150+100*math.sin(pygame.time.get_ticks()*0.008))
                pygame.draw.rect(screen,(pulse,0,0),(bx3-3,MY+6,6,MH-12))
                screen.blit(font_tiny.render("⚠",True,(255,50,50)),(bx3-5,MY+2))
        # Border glow
        alpha_rect(screen,accent,(MX,MY,MW,MH),10)
        pygame.draw.rect(screen,(*accent[:3],80),(MX,MY,MW,MH),1)
        # Legend (tiny)
        legends=[("T","Trader",(255,200,30)),("!","Trial",(180,80,255)),("R","Relic",(60,160,255))]
        for li,(sym,lbl,lcol) in enumerate(legends):
            lx=MX+4+li*80; ly=MY+MH+2
            screen.blit(font_tiny.render(f"{sym}={lbl}",True,lcol),(lx,ly))

    def _heart(self,cx,cy,r):
        pts=[]
        for i in range(30):
            t=math.pi*2*i/30-math.pi/2
            x=cx+r*16*math.sin(t)**3/16; y=cy-r*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16
            pts.append((x,y))
        return pts
    def _star(self,cx,cy,r):
        pts=[]
        for i in range(8): a=math.pi*2*i/8;ri=r if i%2==0 else r*0.45; pts.append((cx+math.cos(a)*ri,cy+math.sin(a)*ri))
        return pts

    def draw_menu(self):
        biome=BIOMES[0]  # always forest on menu
        accent=biome["accent"]
        self.bg.draw(screen,0,0,biome)
        ticks=pygame.time.get_ticks()
        title=font_title.render("BHAVNOBI",True,accent)
        glow=font_title.render("BHAVNOBI",True,accent); glow.set_alpha(int(50+35*math.sin(ticks*0.002)))
        tx=WIDTH//2-title.get_width()//2;ty=HEIGHT//2-175
        screen.blit(glow,(tx+3,ty+3));screen.blit(title,(tx,ty))
        screen.blit(font_med.render("INFINITE RUNNER",True,(55,55,55)),(WIDTH//2-70,HEIGHT//2-90))
        lw=260; pygame.draw.line(screen,accent,(WIDTH//2-lw//2,HEIGHT//2-66),(WIDTH//2+lw//2,HEIGHT//2-66),1)
        lines=[("WASD","Move & Jump"),("Shift","Dash"),("Z","Sword Slash"),("X","Throw Shuriken"),
               ("C (hold)","Shield — blocks projectiles"),("E","Talk to Trader / Start Trial"),
               ("I","Open Inventory"),("1-5","Use hotbar item"),
               ("B","Build mode — place/break blocks with mouse"),
               ("Stomp","Land on enemy head to kill"),("Kill enemies","Earn gold to trade")]
        for i,(k,d) in enumerate(lines):
            ks=font_small.render(k,True,accent);ds=font_small.render("—  "+d,True,(65,65,65))
            screen.blit(ks,(WIDTH//2-175,HEIGHT//2-52+i*22));screen.blit(ds,(WIDTH//2-60,HEIGHT//2-52+i*22))
        # Biome icons row
        biome_y=HEIGHT//2+175
        for i,b in enumerate(BIOMES):
            bx=WIDTH//2-120+i*60
            bi2=font_med.render(b["icon"],True,(180,180,180))
            screen.blit(bi2,(bx,biome_y))
            bn=font_tiny.render(b["name"],True,(50,50,50))
            screen.blit(bn,(bx+bi2.get_width()//2-bn.get_width()//2,biome_y+26))
        pulse=int(180+60*math.sin(ticks*0.004))
        enter=font_med.render("PRESS ENTER TO START",True,accent); enter.set_alpha(pulse)
        screen.blit(enter,(WIDTH//2-enter.get_width()//2,HEIGHT//2+210))
        if self.high_score>0:
            hs=font_small.render(f"Best Score: {self.high_score:06d}",True,(55,55,55))
            screen.blit(hs,(WIDTH//2-hs.get_width()//2,HEIGHT//2+238))

    def draw_dead(self):
        ov=pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((0,0,0,190)); screen.blit(ov,(0,0))
        accent=get_biome(self.cam_x)["accent"]; ticks=pygame.time.get_ticks()
        pw=480;ph=310;px=WIDTH//2-pw//2;py=HEIGHT//2-ph//2
        pygame.draw.rect(screen,(10,10,18),(px,py,pw,ph))
        pygame.draw.rect(screen,accent,(px,py,pw,ph),1);alpha_rect(screen,accent,(px,py,pw,ph),10)
        pygame.draw.rect(screen,accent,(px+5,py+5,pw-10,ph-10),1)
        t1=font_big.render("YOU DIED!",True,(226,75,74)); screen.blit(t1,(WIDTH//2-t1.get_width()//2,py+28))
        t2=font_med.render(f"SCORE   {int(self.score):06d}",True,(200,200,200)); screen.blit(t2,(WIDTH//2-t2.get_width()//2,py+80))
        t2b=font_small.render(f"Gold earned this run: {self.player.gold}",True,(255,200,30)); screen.blit(t2b,(WIDTH//2-t2b.get_width()//2,py+112))
        nb=int(self.score)>=self.high_score and self.high_score>0
        t3=font_small.render("★ NEW BEST!" if nb else f"BEST  {self.high_score:06d}",True,accent if nb else(65,65,65))
        screen.blit(t3,(WIDTH//2-t3.get_width()//2,py+140))
        if self.combo>1:
            t4=font_small.render(f"Max Combo  x{self.combo}",True,(239,159,39)); screen.blit(t4,(WIDTH//2-t4.get_width()//2,py+164))
        pygame.draw.line(screen,(38,38,38),(px+30,py+192),(px+pw-30,py+192),1)
        pulse=int(180+60*math.sin(ticks*0.005))
        t5=font_med.render("PRESS ENTER TO PLAY AGAIN",True,accent); t5.set_alpha(pulse)
        screen.blit(t5,(WIDTH//2-t5.get_width()//2,py+208))

def main():
    game=Game();game.state="menu"
    while True:
        raw=pygame.key.get_pressed();just={}
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit();sys.exit()
            if event.type==pygame.MOUSEBUTTONDOWN:
                if game.inv_ui.open:
                    game.inv_ui.handle_mouse(event.pos,event.button,game.player)
                elif game.state=="playing" and game.build_mode and not game.shop_ui.open:
                    # Build mode mouse clicks — use same cx/cy as the renderer
                    mx,my=event.pos
                    cx=int(game.cam_x)+int(game.shake_off[0])
                    cy=int(game.cam_y)+int(game.shake_off[1])
                    world_mx=mx+cx; world_my=my+cy
                    gx=int(world_mx//BLOCK_SIZE); gy=int(world_my//BLOCK_SIZE)
                    if event.button==1:  # left click = place block
                        d=BLOCK_TYPES[game.build_type]
                        new_rect=pygame.Rect(gx*BLOCK_SIZE,gy*BLOCK_SIZE,BLOCK_SIZE,BLOCK_SIZE)
                        overlap=any(b.gx==gx and b.gy==gy for b in game.placed_blocks)
                        plat_overlap=any(new_rect.colliderect(p.rect()) for p in game.platforms)
                        if not overlap and not plat_overlap and len(game.placed_blocks)<100:
                            if game.player.gold>=d["cost"]:
                                game.player.gold-=d["cost"]
                                game.placed_blocks.append(PlacedBlock(gx,gy,game.build_type))
                            else:
                                game.dmg_nums.append(DmgNum(
                                    game.player.x,game.player.y-20,
                                    f"Need {d['cost']}g!",(220,80,80)))
                    elif event.button==3:  # right click = break nearest block to cursor
                        best_i=None; best_dist=BLOCK_SIZE*1.2
                        for i,b in enumerate(game.placed_blocks):
                            # Block centre in screen coords
                            bsx=b.x+BLOCK_SIZE//2-cx
                            bsy=b.y+BLOCK_SIZE//2-cy
                            dist=math.hypot(mx-bsx, my-bsy)
                            if dist<best_dist:
                                best_dist=dist; best_i=i
                        if best_i is not None:
                            b=game.placed_blocks[best_i]
                            refund=BLOCK_TYPES[b.btype]["refund"]
                            game.player.gold+=refund
                            game._ptcl(b.x+BLOCK_SIZE//2,b.y+BLOCK_SIZE//2,
                                       BLOCK_TYPES[b.btype]["color"],6,3,0.5)
                            game.placed_blocks.pop(best_i)
            if event.type==pygame.KEYDOWN:
                just[event.key]=True
                if event.key==pygame.K_ESCAPE:
                    if game.build_mode: game.build_mode=False
                    elif game.shop_ui.open: game.shop_ui.close()
                    elif game.inv_ui.open: game.inv_ui.open=False
                    else: pygame.quit();sys.exit()
                if event.key==pygame.K_b and game.state=="playing":
                    game.build_mode=not game.build_mode
                    game.inv_ui.open=False; game.shop_ui.close()
                if event.key==pygame.K_i and game.state=="playing":
                    game.inv_ui.open=not game.inv_ui.open
                    if game.inv_ui.open: game.build_mode=False
                # D in build mode = delete hovered block
                if event.key==pygame.K_d and game.build_mode and game.state=="playing":
                    if game.build_preview:
                        gx_h,gy_h=game.build_preview
                        for i,b in enumerate(game.placed_blocks):
                            if b.gx==gx_h and b.gy==gy_h:
                                refund=BLOCK_TYPES[b.btype]["refund"]
                                game.player.gold+=refund
                                game._ptcl(b.x+BLOCK_SIZE//2,b.y+BLOCK_SIZE//2,
                                           BLOCK_TYPES[b.btype]["color"],6,3,0.5)
                                game.placed_blocks.pop(i)
                                game.dmg_nums.append(DmgNum(
                                    game.player.x,game.player.y-20,
                                    f"+{refund}g refund",(255,200,30)))
                                break
                if game.shop_ui.open: game.shop_ui.handle_key(event.key,game.player)
                elif game.inv_ui.open: game.inv_ui.handle_key(event.key,game.player)
                if event.key in(pygame.K_RETURN,pygame.K_KP_ENTER):
                    if game.state=="menu": game.reset();game.state="playing"
                    elif game.state=="dead": game.reset();game.state="playing"
        if game.state=="playing":   game.update(raw,just);game.draw()
        elif game.state=="menu":    game.draw_menu()
        elif game.state=="dead":    game.draw();game.draw_dead()
        pygame.display.flip();clock.tick(FPS)

if __name__=="__main__":
    main()