import pygame, random, sys
pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Nana Game")
clock = pygame.time.Clock()

WHITE = (255,255,255)
RED = (255,80,80)
BLUE = (80,180,255)
YELLOW = (255,220,120)
ORANGE = (255,140,0)
CYAN = (120,255,255)
BLACK = (10,10,20)

font_big = pygame.font.SysFont("arial",70)
font = pygame.font.SysFont("arial",30)
font_small = pygame.font.SysFont("arial",22)

player = pygame.Rect(120, HEIGHT//2, 24, 16)
player_speed = 6
player_alive = True

gun_modes = {1: {"cooldown":40,"speed":8,"damage":5},
             2: {"cooldown":18,"speed":9,"damage":3},
             3: {"cooldown":5,"speed":12,"damage":1}}

current_gun = 2
cooldown = 0

bullets = []
enemy_bullets = []
enemies = []
explosions = []
flames = []

wave = 1
wave_enemy_total = 0
wave_killed = 0

stars = [[random.randint(0,WIDTH), random.randint(0,HEIGHT), random.randint(1,2)] for _ in range(100)]

class Explosion:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.r = 4
    def update(self):
        self.r += 2
    def draw(self,s):
        pygame.draw.rect(s,YELLOW,(self.x-self.r//2,self.y-self.r//2,self.r,self.r))
        pygame.draw.rect(s,ORANGE,(self.x-self.r//4,self.y-self.r//4,self.r//2,self.r//2))
    def done(self):
        return self.r>32

def spawn_wave(w):
    global wave_enemy_total
    wave_enemy_total = w
    for _ in range(w):
        y = random.randint(20, HEIGHT-36)
        enemies.append({"rect":pygame.Rect(WIDTH+random.randint(0,200),y,24,16),"health":5})

def restart_wave():
    global enemies, bullets, enemy_bullets, wave_killed
    enemies = []
    bullets = []
    enemy_bullets = []
    wave_killed = 0
    spawn_wave(wave)

def reset_game():
    global bullets, enemy_bullets, enemies, explosions, flames, wave, player_alive, wave_killed
    bullets=[]
    enemy_bullets=[]
    enemies=[]
    explosions=[]
    flames=[]
    wave=1
    wave_killed=0
    player_alive=True
    player.y=HEIGHT//2
    spawn_wave(wave)

def draw_player(s,r):
    x,y,w,h=r
    for f in flames:
        pygame.draw.rect(s,f[2],(f[0][0],f[0][1],f[1],f[1]))
    # body
    pygame.draw.polygon(s, BLUE, [(x+w, y+h//2),(x, y),(x, y+h)])
    # cockpit
    pygame.draw.rect(s,CYAN,(x+w-6, y+h//2-2,4,4))
    # top wing
    pygame.draw.polygon(s, BLUE, [(x+6, y+2),(x+12, y+h//2),(x+6, y+h//2-2)])
    # bottom wing
    pygame.draw.polygon(s, BLUE, [(x+6, y+h-2),(x+12, y+h//2),(x+6, y+h//2+2)])

def draw_enemy(s,r):
    x,y,w,h=r
    # body
    pygame.draw.polygon(s, RED, [(x, y+h//2),(x+w, y),(x+w, y+h)])
    # cockpit
    pygame.draw.rect(s,(200,50,50),(x+2,y+h//2-2,4,4))
    # top wing
    pygame.draw.polygon(s, RED, [(x+w-6, y+2),(x+w-12, y+h//2),(x+w-6, y+h//2-2)])
    # bottom wing
    pygame.draw.polygon(s, RED, [(x+w-6, y+h-2),(x+w-12, y+h//2),(x+w-6, y+h//2+2)])

def spawn_flame():
    offset_y=random.randint(-4,4)
    size=random.randint(2,4)
    color=random.choice([YELLOW,ORANGE])
    x=player.x-4
    y=player.centery+offset_y
    flames.append([[x,y],size,color])

def update_flames():
    for f in flames[:]:
        f[0][0]-=4
        f[1]-=0.1
        if f[1]<=0:
            flames.remove(f)

spawn_wave(wave)

while True:
    clock.tick(60)
    screen.fill(BLACK)

    for star in stars:
        star[0]-=star[2]
        if star[0]<0:
            star[0]=WIDTH
            star[1]=random.randint(0,HEIGHT)
        pygame.draw.rect(screen,(200,200,255),(star[0],star[1],star[2],star[2]))

    for event in pygame.event.get():
        if event.type==pygame.QUIT: sys.exit()
        if event.type==pygame.KEYDOWN:
            if player_alive:
                if event.key==pygame.K_1: current_gun=1
                if event.key==pygame.K_2: current_gun=2
                if event.key==pygame.K_3: current_gun=3
            if not player_alive and event.key==pygame.K_r:
                reset_game()

    keys=pygame.key.get_pressed()
    if player_alive:
        if keys[pygame.K_UP]: player.y-=player_speed
        if keys[pygame.K_DOWN]: player.y+=player_speed
        player.y=max(0,min(HEIGHT-player.height,player.y))
        if cooldown<=0:
            bullets.append({"rect":pygame.Rect(player.right,player.centery-2,6,6),"damage":gun_modes[current_gun]["damage"]})
            cooldown=gun_modes[current_gun]["cooldown"]
        spawn_flame()
    cooldown-=1
    update_flames()

    for bullet in bullets[:]:
        bullet["rect"].x+=gun_modes[current_gun]["speed"]
        if bullet["rect"].x>WIDTH: bullets.remove(bullet)

    for enemy in enemies[:]:
        enemy["rect"].x-=2+wave*0.25
        if random.randint(0,130)==1:
            enemy_bullets.append(pygame.Rect(enemy["rect"].left,enemy["rect"].centery,6,6))
        if enemy["rect"].right<0:
            restart_wave()
            break

    for eb in enemy_bullets[:]:
        eb.x-=6
        if eb.x<0: enemy_bullets.remove(eb)
        if player_alive and eb.colliderect(player):
            explosions.append(Explosion(player.centerx,player.centery))
            player_alive=False

    for bullet in bullets[:]:
        for enemy in enemies[:]:
            if bullet["rect"].colliderect(enemy["rect"]):
                enemy["health"]-=bullet["damage"]
                if bullet in bullets: bullets.remove(bullet)
                if enemy["health"]<=0:
                    explosions.append(Explosion(enemy["rect"].centerx,enemy["rect"].centery))
                    enemies.remove(enemy)
                    wave_killed+=1

    if player_alive and wave_killed==wave_enemy_total:
        wave+=1
        wave_killed=0
        spawn_wave(wave)

    for e in explosions[:]:
        e.update()
        e.draw(screen)
        if e.done(): explosions.remove(e)

    if player_alive: draw_player(screen,player)
    for enemy in enemies: draw_enemy(screen,enemy["rect"])
    for bullet in bullets: pygame.draw.rect(screen,WHITE,bullet["rect"])
    for eb in enemy_bullets: pygame.draw.rect(screen,ORANGE,eb)

    text=font.render(f"WAVE {wave}   GUN {current_gun}",True,WHITE)
    screen.blit(text,(10,10))

    if not player_alive:
        overlay=pygame.Surface((WIDTH,HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay,(0,0))
        title=font_big.render("GAME OVER",True,RED)
        screen.blit(title,(WIDTH//2-title.get_width()//2,180))
        waves=font.render(f"You survived {wave} waves",True,WHITE)
        screen.blit(waves,(WIDTH//2-waves.get_width()//2,280))
        restart=font_small.render("Press R to restart",True,(200,200,200))
        screen.blit(restart,(WIDTH//2-restart.get_width()//2,340))

    pygame.display.update()