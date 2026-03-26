from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import math

app = Ursina()

player = FirstPersonController(y=2, origin_y=-.5, jump_height=3.5, gravity=0.7, speed=11)
player.hp = 3

sword = Entity(parent=camera, position=(0.5, -0.45, 0.9), rotation=(10, -10, 0))

blade  = Entity(model='cube', parent=sword, scale=(0.02, 1.0, 0.008), color=color.rgb(255,210,0), y=0.38)
fuller = Entity(model='cube', parent=blade, scale=(0.3, 0.92, 2.0),   color=color.rgb(255,240,100))
guard  = Entity(model='cube', parent=sword, scale=(0.35, 0.02, 0.02),  color=color.rgb(200,150,0), y=0.0)
guard_l= Entity(model='cube', parent=guard, scale=(0.08, 2.5, 2.0),    color=color.rgb(220,170,0), x=-0.52)
guard_r= Entity(model='cube', parent=guard, scale=(0.08, 2.5, 2.0),    color=color.rgb(220,170,0), x= 0.52)
handle = Entity(model='cube', parent=sword, scale=(0.025, 0.24, 0.025),color=color.rgb(80,40,10),  y=-0.14)
pommel = Entity(model='cube', parent=sword, scale=(0.06, 0.04, 0.06),  color=color.rgb(200,150,0), y=-0.28)

sword_base_pos = Vec3(0.5, -0.45, 0.9)
sword_base_rot = Vec3(10, -10, 0)
sword_idle_t   = 0
is_swinging    = False
swing_t        = 0

HEART_PIXEL = [
    [0,1,1,0,1,1,0],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [0,1,1,1,1,1,0],
    [0,0,1,1,1,0,0],
    [0,0,0,1,0,0,0],
]

HUD_X      = -0.87
HUD_Y      =  0.44
PIXEL_SIZE =  0.009

Text(parent=camera.ui, text='HP', position=(HUD_X-0.005, HUD_Y+0.008),
     scale=1.4, color=color.rgb(255,80,80), font='VeraMono.ttf')

def make_pixel_heart(index):
    root = Entity(parent=camera.ui, position=(HUD_X+0.1 + index*0.09, HUD_Y+0.005))
    pixels = []
    for row_i, row in enumerate(HEART_PIXEL):
        for col_i, filled in enumerate(row):
            if filled:
                px = Entity(
                    parent=camera.ui,
                    model='quad',
                    color=color.rgb(220, 30, 50),
                    scale=(PIXEL_SIZE, PIXEL_SIZE),
                    position=(
                        root.x + (col_i - 3) * PIXEL_SIZE,
                        root.y - row_i * PIXEL_SIZE
                    ),
                    z=0
                )
                pixels.append(px)
    root.pixels = pixels
    return root

hearts = [make_pixel_heart(i) for i in range(3)]

def set_heart_enabled(index, enabled):
    for px in hearts[index].pixels:
        px.enabled = enabled

score      = 0
high_score = 0

score_text      = Text(text=f'Score: {score}',           position=(-0.85, 0.345), scale=2,   color=color.yellow)
high_score_text = Text(text=f'High Score: {high_score}', position=(-0.85, 0.295), scale=1.5, color=color.white)

death_screen = Entity(parent=camera.ui, model='quad', scale=(2,2), color=color.black90, enabled=False)
Text(parent=death_screen, text='YOU DIED', origin=(0,0), scale=5, color=color.red)

platforms    = []
enemies      = []
last_spawn_z = 0

SKIN  = color.rgb(100, 200, 100)
SHIRT = color.rgb(100, 200, 100)
PANTS = color.gold
SHOE  = color.gold

def spawn_character(x, y, z):
    root = Entity(x=x, y=y, z=z, collider='box', scale=(0.8, 1.8, 0.8))

    leg_l = Entity(model='cube', parent=root, color=PANTS,
                   scale=(0.35, 0.7, 0.35), x=-0.18, y=-0.18)
    leg_r = Entity(model='cube', parent=root, color=PANTS,
                   scale=(0.35, 0.7, 0.35), x= 0.18, y=-0.18)
    Entity(model='cube', parent=leg_l, color=SHOE,
           scale=(1.0, 0.25, 1.5), y=-0.52, z=0.1)
    Entity(model='cube', parent=leg_r, color=SHOE,
           scale=(1.0, 0.25, 1.5), y=-0.52, z=0.1)

    body = Entity(model='cube', parent=root, color=SHIRT,
                  scale=(0.7, 0.7, 0.5), y=0.38)

    arm_l = Entity(model='cube', parent=root, color=SKIN,
                   scale=(0.25, 0.6, 0.25), x=-0.48, y=0.32)
    arm_r = Entity(model='cube', parent=root, color=SKIN,
                   scale=(0.25, 0.6, 0.25), x= 0.48, y=0.32)

    head = Entity(model='cube', parent=root, color=SKIN,
                  scale=(0.55, 0.55, 0.5), y=0.82)

    eye_l = Entity(model='cube', parent=head, color=color.white,
                scale=(0.3, 0.3, 0.2), x=-0.25, y=0.1, z=-0.52, eternal=True)
    eye_r = Entity(model='cube', parent=head, color=color.white,
                scale=(0.3, 0.3, 0.2), x= 0.25, y=0.1, z=-0.52, eternal=True)
    Entity(model='cube', parent=head, color=color.black, scale=(0.15, 0.15, 0.12), x=-0.25, y=0.1, z=-0.65)
    Entity(model='cube', parent=head, color=color.black, scale=(0.15, 0.15, 0.12), x= 0.25, y=0.1, z=-0.65)
    Entity(model='cube', parent=head, color=color.rgb(180,20,20),
           scale=(0.5, 0.1, 0.2), y=-0.25, z=-0.52)

    root.walk_dir = 1
    root.start_x  = x
    root.walk_t   = random.uniform(0, math.pi * 2)
    root.arm_l    = arm_l
    root.arm_r    = arm_r
    root.leg_l    = leg_l
    root.leg_r    = leg_r
    root.body     = body

    enemies.append(root)

def spawn_platform(z):
    p = Entity(model='cube', texture='brick', scale=(8,0.5,8),
               x=random.uniform(-6,6), y=random.uniform(-0.5,1.5),
               z=z, collider='box', color=color.orange)
    platforms.append(p)
    if random.random() > 0.6:
        spawn_character(p.x, p.y + 1.4, p.z)

def reset_game():
    global last_spawn_z, score, high_score
    if score > high_score:
        high_score = score
        high_score_text.text = f'High Score: {high_score}'
    death_screen.enabled = True
    invoke(setattr, death_screen, 'enabled', False, delay=2)
    player.position = (0, 5, 0)
    player.hp = 3
    for i in range(3): set_heart_enabled(i, True)
    for p in platforms + enemies: destroy(p)
    platforms.clear(); enemies.clear()
    last_spawn_z = 0; score = 0
    score_text.text = f'Score: {score}'
    spawn_platform(0)

def input(key):
    global is_swinging, swing_t
    if key == 'left mouse down' and not death_screen.enabled and not is_swinging:
        is_swinging = True
        swing_t = 0
        for e in enemies[:]:
            if distance(player, e) < 5:
                enemies.remove(e)
                destroy(e)

spawn_platform(0)

def update():
    global last_spawn_z, score, sword_idle_t, is_swinging, swing_t

    if death_screen.enabled: return

    sword_idle_t += time.dt

    if is_swinging:
        swing_t += time.dt
        progress = swing_t / 0.3
        if progress < 0.5:
            t = progress / 0.5
            sword.position = sword_base_pos + Vec3(-0.08*t, 0.12*t, -0.04*t)
            sword.rotation = sword_base_rot + Vec3(-60*t, 10*t, -20*t)
        elif progress < 1.0:
            t = (progress - 0.5) / 0.5
            sword.position = sword_base_pos + Vec3(-0.08*(1-t), 0.12*(1-t), -0.04*(1-t))
            sword.rotation = sword_base_rot + Vec3(-60*(1-t), 10*(1-t), -20*(1-t))
        else:
            is_swinging = False
            sword.position = sword_base_pos
            sword.rotation = sword_base_rot
    else:
        sword.position = sword_base_pos + Vec3(
            math.sin(sword_idle_t * 1.4) * 0.005,
            math.sin(sword_idle_t * 1.8) * 0.003,
            0
        )
        sword.rotation = sword_base_rot + Vec3(
            math.sin(sword_idle_t * 1.2) * 0.7,
            math.cos(sword_idle_t * 0.9) * 0.5,
            math.sin(sword_idle_t * 1.5) * 0.3
        )

    if player.z > last_spawn_z - 25:
        last_spawn_z += 10
        spawn_platform(last_spawn_z)
        score += 1
        score_text.text = f'Score: {score}'

    for e in enemies[:]:
        e.walk_t += time.dt * 4
        swing = math.sin(e.walk_t) * 20

        e.leg_l.rotation_x =  swing
        e.leg_r.rotation_x = -swing
        e.arm_l.rotation_x = -swing
        e.arm_r.rotation_x =  swing

        e.x += e.walk_dir * time.dt * 2
        if abs(e.x - e.start_x) > 3:
            e.walk_dir *= -1

        e.rotation_y = 180 if (player.x - e.x) > 0 else 0

        if distance(player, e) < 2:
            player.hp -= 1
            if player.hp >= 0:
                set_heart_enabled(int(player.hp), False)
            e.z -= 10

    if player.y < -15 or player.hp <= 0:
        reset_game()

app.run()