def game1():
    def B127():
        import pygame
        import os
        import random
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()
        font = pygame.font.SysFont("pixelify sans", 36, True)
        big_font = pygame.font.SysFont("pixelify sans", 80, True)
        timer_font = pygame.font.SysFont("pixelify sans", 28, True)
        medium_font = pygame.font.SysFont("pixelify sans", 48, True)
        small_font = pygame.font.SysFont("pixelify sans", 24, True)
        screen_w, screen_h = 698, 700
        screen = pygame.display.set_mode((screen_w, screen_h))
        clock = pygame.time.Clock()
        blue = (135, 206, 235)
        FPS = 60
        EFFECT_TIME = 60 * FPS
        def load_high_score():
            try:
                with open("high_score.txt", "r") as f:
                    return int(f.read())
            except:
                return 0
        def save_high_score(score):
            with open("high_score.txt", "w") as f:
                f.write(str(score))
        score = 0
        final_score = 0
        high_score = load_high_score()
        game_over = False
        BASE_DIR = os.path.dirname(__file__)
        IMG_DIR = os.path.join(BASE_DIR, "images")
        SOUND_DIR = os.path.join(BASE_DIR, "sounds")
        platform_img = pygame.image.load(os.path.join(IMG_DIR, "stone.png")).convert_alpha()
        red_img = pygame.image.load(os.path.join(IMG_DIR, "red.png")).convert_alpha()
        maroon_img = pygame.image.load(os.path.join(IMG_DIR, "maroon.png")).convert_alpha()
        turquoise_img = pygame.image.load(os.path.join(IMG_DIR, "turquoise.png")).convert_alpha()
        blue_img = pygame.image.load(os.path.join(IMG_DIR, "blue.png")).convert_alpha()
        player_img = pygame.image.load(os.path.join(IMG_DIR, "player.png")).convert_alpha()
        enemy_img = pygame.image.load(os.path.join(IMG_DIR, "enemy.png")).convert_alpha()
        white_img = pygame.Surface(platform_img.get_size(), pygame.SRCALPHA)
        white_img.fill((255, 255, 255, 255))
        powerup_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "powerup.wav"))
        walk_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "walk.wav"))
        jump_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "jump.wav"))
        enemy_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "enemy_hit.wav"))
        slow_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "slow.wav"))
        game_over_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "game_over.wav"))
        pygame.mixer.music.load(os.path.join(SOUND_DIR, "music.mp3"))
        pygame.mixer.music.play(-1)
        walk_channel = pygame.mixer.Channel(1)
        enemy_channel = pygame.mixer.Channel(2)
        class Player(pygame.sprite.Sprite):
            def __init__(self):
                super().__init__()
                self.original_image = player_img
                self.image = self.original_image
                self.rect = self.image.get_rect(midbottom=(screen_w // 2, screen_h - 50))
                self.change_x = 0
                self.change_y = 0
                self.gravity = 0.8
                self.base_jump = -20
                self.jump_speed = self.base_jump
                self.jump_timer = 0
                self.base_speed = 6
                self.speed = self.base_speed
                self.speed_timer = 0
                self.angle = 0
                self.last_kill_time = 0
            def update(self, platforms):
                nonlocal score, game_over, final_score, high_score
                if self.speed_timer > 0:
                    self.speed_timer -= 1
                    if self.speed_timer == 0:
                        self.speed = self.base_speed
                if self.jump_timer > 0:
                    self.jump_timer -= 1
                    if self.jump_timer == 0:
                        self.jump_speed = self.base_jump
                self.change_y += self.gravity
                self.rect.y += self.change_y
                if self.change_y > 0:
                    hits = pygame.sprite.spritecollide(self, platforms, False)
                    if hits:
                        plat = hits[0]
                        self.rect.bottom = plat.rect.top
                        self.change_y = 0
                        if not plat.used:
                            if plat.kind == "maroon":
                                self.speed = 2
                                self.speed_timer = EFFECT_TIME
                                slow_snd.play()
                            elif plat.kind == "turquoise":
                                self.jump_speed = -30
                                self.jump_timer = EFFECT_TIME
                                powerup_snd.play()
                            elif plat.kind == "blue":
                                self.speed = 12
                                self.speed_timer = EFFECT_TIME
                                powerup_snd.play()
                            elif plat.kind == "red":
                                score -= 20
                            plat.used = True
                self.rect.x += self.change_x
                if self.rect.top > screen_h:
                    game_over = True
                    final_score = score
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
                    game_over_snd.play()
                    pygame.mixer.music.stop()
            def jump(self, platforms):
                self.rect.y += 2
                hits = pygame.sprite.spritecollide(self, platforms, False)
                self.rect.y -= 2
                if hits:
                    self.change_y = self.jump_speed
                    jump_snd.play()
        class Platform(pygame.sprite.Sprite):
            def __init__(self, x, y, w, img, kind):
                super().__init__()
                self.image = pygame.transform.scale(img, (w, 15))
                self.rect = self.image.get_rect(topleft=(x, y))
                self.kind = kind
                self.used = False
                self.scored = False
        class Enemy(pygame.sprite.Sprite):
            def __init__(self, platform):
                super().__init__()
                self.image = pygame.transform.scale(enemy_img, (60, 60))
                self.rect = self.image.get_rect(midbottom=(platform.rect.centerx, platform.rect.top))
                self.platform = platform
                self.direction = random.choice([-1, 1])
                self.speed = 2
            def update(self, scroll):
                self.rect.y += scroll
                self.rect.x += self.direction * self.speed
                if self.rect.left < self.platform.rect.left or self.rect.right > self.platform.rect.right:
                    self.direction *= -1
                if self.rect.top > screen_h:
                    self.kill()
        player = None
        platforms = None
        enemies = None
        def reset_game():
            nonlocal score, final_score, game_over, player, platforms, enemies
            score = 0
            final_score = 0
            game_over = False
            player = Player()
            platforms = pygame.sprite.Group()
            enemies = pygame.sprite.Group()
            platforms.add(Platform(0, screen_h - 20, screen_w, white_img, "normal"))
            for i in range(10):
                w = random.randint(100, 160)
                x = random.randint(0, screen_w - w)
                y = i * 70 + 50
                platforms.add(Platform(x, y, w, platform_img, "normal"))
        reset_game()
        running = True
        frame_count = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if not game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        player.jump(platforms)
                if game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        reset_game()
                        pygame.mixer.music.play(-1)
            screen.fill(blue)
            if not game_over:
                keys = pygame.key.get_pressed()
                player.change_x = 0
                if keys[pygame.K_LEFT]:
                    player.change_x = -player.speed
                if keys[pygame.K_RIGHT]:
                    player.change_x = player.speed
                if player.change_x != 0 and player.change_y == 0:
                    if not walk_channel.get_busy():
                        walk_channel.play(walk_snd)
                else:
                    walk_channel.stop()
                if keys[pygame.K_a]:
                    player.angle += 20
                    cx, b = player.rect.centerx, player.rect.bottom
                    player.image = pygame.transform.rotate(player.original_image, player.angle)
                    player.rect = player.image.get_rect(centerx=cx, bottom=b)
                    killed = pygame.sprite.spritecollide(player, enemies, True)
                    if killed:
                        score += 5
                        if frame_count - player.last_kill_time > 10:
                            enemy_channel.play(enemy_snd)
                            player.last_kill_time = frame_count
                else:
                    player.angle = 0
                    cx, b = player.rect.centerx, player.rect.bottom
                    player.image = player.original_image
                    player.rect = player.image.get_rect(centerx=cx, bottom=b)
                    if pygame.sprite.spritecollide(player, enemies, False):
                        game_over = True
                        final_score = score
                        if score > high_score:
                            high_score = score
                            save_high_score(high_score)
                        game_over_snd.play()
                        pygame.mixer.music.stop()
                player.update(platforms)
                scroll = 0
                if player.rect.top <= 200:
                    scroll = 200 - player.rect.top
                    player.rect.y += scroll
                    for p in platforms:
                        p.rect.y += scroll
                        if p.rect.top >= screen_h and not p.scored:
                            p.scored = True
                            score += 1
                            p.kill()
                enemies.update(scroll)
                while len(platforms) < 10:
                    w = random.randint(100, 160)
                    x = random.randint(0, screen_w - w)
                    y = min(p.rect.y for p in platforms) - random.randint(80, 110)
                    r = random.randint(1, 100)
                    img, kind = platform_img, "normal"
                    if r <= 8:
                        img, kind = turquoise_img, "turquoise"
                    elif r <= 10:
                        img, kind = blue_img, "blue"
                    elif r <= 20:
                        img, kind = red_img, "red"
                    elif r <= 33:
                        img, kind = maroon_img, "maroon"
                    new_p = Platform(x, y, w, img, kind)
                    platforms.add(new_p)
                    if random.random() < 0.2:
                        enemies.add(Enemy(new_p))
                platforms.draw(screen)
                enemies.draw(screen)
                screen.blit(player.image, player.rect)
                screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
                screen.blit(font.render(f"High Score: {high_score}", True, (255, 255, 255)), (10, 50))
                if player.speed_timer > 0:
                    secs = player.speed_timer // FPS
                    if player.speed < player.base_speed:
                        screen.blit(
                            timer_font.render(f"Slow: {secs//60}:{secs%60:02d}", True, (255, 100, 100)),
                            (screen_w - 180, 10)
                        )
                    else:
                        screen.blit(
                            timer_font.render(f"Speed: {secs//60}:{secs%60:02d}", True, (100, 255, 255)),
                            (screen_w - 180, 10)
                        )
                if player.jump_timer > 0:
                    secs = player.jump_timer // FPS
                    screen.blit(
                        timer_font.render(f"Jump: {secs//60}:{secs%60:02d}", True, (100, 255, 255)),
                        (screen_w - 180, 45)
                    )
            else:
                overlay = pygame.Surface((screen_w, screen_h))
                overlay.set_alpha(180)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
                box_width = 500
                box_height = 350
                box_x = (screen_w - box_width) // 2
                box_y = (screen_h - box_height) // 2
                box_surface = pygame.Surface((box_width, box_height))
                box_surface.fill((40, 40, 60))
                box_surface.set_alpha(240)
                screen.blit(box_surface, (box_x, box_y))
                pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height), 3)
                game_over_text = big_font.render("GAME OVER", True, (255, 80, 80))
                game_over_rect = game_over_text.get_rect(center=(screen_w // 2, box_y + 70))
                screen.blit(game_over_text, game_over_rect)
                score_text = medium_font.render(f"Score: {final_score}", True, (255, 255, 255))
                score_rect = score_text.get_rect(center=(screen_w // 2, box_y + 150))
                screen.blit(score_text, score_rect)
                high_score_text = medium_font.render(f"High Score: {high_score}", True, (255, 255, 255))
                high_score_rect = high_score_text.get_rect(center=(screen_w // 2, box_y + 210))
                screen.blit(high_score_text, high_score_rect)
                restart_text = small_font.render("Press R to Restart", True, (200, 200, 200))
                restart_rect = restart_text.get_rect(center=(screen_w // 2, box_y + 280))
                screen.blit(restart_text, restart_rect)
            pygame.display.flip()
            clock.tick(FPS)
            frame_count += 1
        pygame.quit()
    def race():
        import pygame
        import random
        import pickle
        import os

        pygame.init()
        pygame.mixer.init()
        WIDTH, HEIGHT = 800, 600
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()

        BASE_DIR = os.path.dirname(__file__)
        SOUND_DIR = os.path.join(BASE_DIR, "sounds")
        pygame.mixer.music.load(os.path.join(SOUND_DIR, "music.mp3"))
        pygame.mixer.music.play(-1)
        enemy_channel = pygame.mixer.Channel(2)

        ROAD_WIDTH = 400
        ROAD_LEFT = (WIDTH - ROAD_WIDTH) // 2
        ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
        SPAWN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(SPAWN_EVENT, 1000)

        font_main = pygame.font.SysFont("Arial", 80, bold=True)
        font_sub = pygame.font.SysFont("Arial", 32)
        font_score = pygame.font.SysFont("Arial", 24)

        BASE_DIR = os.path.dirname(__file__)
        IMG_DIR = os.path.join(BASE_DIR, "assets")

        def load_asset(name, width, height, fallback_color):
            path = os.path.join('assets', name)
            try:
                image = pygame.image.load(os.path.join(IMG_DIR, name)).convert_alpha()
                return pygame.transform.scale(image, (width, height))
            except:
                fallback = pygame.Surface((width, height))
                fallback.fill(fallback_color)
                return fallback

        player_img = load_asset('player_car.png', 40, 60, (255, 0, 0))
        enemy_img = load_asset('enemy_car.png', 50, 70, (0, 0, 255))

        HIGH_SCORE_FILE = 'highscore.dat'

        def load_highscore():
            if os.path.exists(HIGH_SCORE_FILE):
                try:
                    with open(HIGH_SCORE_FILE, 'rb') as f:
                        return pickle.load(f)
                except:
                    return 0
            return 0

        def save_highscore(score):
            with open(HIGH_SCORE_FILE, 'wb') as f:
                pickle.dump(score, f)

        highscore = load_highscore()

        def reset_game():
            return (
                player_img.get_rect(center=(WIDTH//2, HEIGHT - 80)),
                [],
                0,
                False
            )

        player_rect, enemies, score, game_over = reset_game()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
                if event.type == SPAWN_EVENT and not game_over:
                    enemy_rect = enemy_img.get_rect(center=(random.randint(ROAD_LEFT + 15, ROAD_RIGHT - 15), -100))
                    enemies.append(enemy_rect)
            
                if event.type == pygame.KEYDOWN and game_over:
                    if event.key == pygame.K_r:
                        player_rect, enemies, score, game_over = reset_game()

            if not game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] and player_rect.left > ROAD_LEFT: player_rect.x -= 7
                if keys[pygame.K_RIGHT] and player_rect.right < ROAD_RIGHT: player_rect.x += 7

                score += 1
                for enemy in enemies[:]:
                    enemy.y += 7
                    if enemy.top > HEIGHT: enemies.remove(enemy)
                    if player_rect.colliderect(enemy): 
                        game_over = True
                        if score > highscore:
                            highscore = score
                            save_highscore(highscore)

            screen.fill((34, 139, 34))
            pygame.draw.rect(screen, (50, 50, 50), (ROAD_LEFT, 0, ROAD_WIDTH, HEIGHT))
        
            for enemy in enemies:
                screen.blit(enemy_img, enemy)
            
            screen.blit(player_img, player_rect)

            score_surf = font_score.render(f"Score: {score}", True, (255, 255, 255))
            screen.blit(score_surf, (10, 10))

            if game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                screen.blit(overlay, (0, 0))
                enemy_snd = pygame.mixer.Sound(os.path.join(SOUND_DIR, "enemy_hit.wav"))
                enemy_channel.play(enemy_snd)

                go_surf = font_main.render("GAME OVER", True, (255, 50, 50))
                sc_surf = font_sub.render(f"Final Score: {score}", True, (255, 255, 255))
                hs_surf = font_sub.render(f"High Score: {highscore}", True, (255, 255, 100))
                re_surf = font_sub.render("Press 'R' to Restart", True, (200, 200, 200))

                screen.blit(go_surf, go_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 90)))
                screen.blit(sc_surf, sc_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 10)))
                screen.blit(hs_surf, hs_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))
                screen.blit(re_surf, re_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 100)))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
    def pixel():
        import pygame

        pygame.init()
        WIDTH, HEIGHT = 1000, 700
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pro Pixel Art Tool")
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 18)

        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GRAY_LINE = (200, 200, 200)
        BG = (40, 40, 40)

        BASE_PIXEL_SIZE = 20
        zoom = 1.0
        camera_x, camera_y = 0, 0

        grid = {}

        picker_x, picker_y = 650, 50
        picker_size = 255

        hue = 0
        sat = 100
        val = 100

        current_color = pygame.Color(0)
        current_color.hsva = (hue, sat, val, 100)

        selector_sb = [picker_x, picker_y]
        selector_hue = [945, picker_y]

        running = True
        while running:
            screen.fill(BG)
            mx, my = pygame.mouse.get_pos()
            m_press = pygame.mouse.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEWHEEL:
                    zoom += event.y * 0.1
                    zoom = max(0.2, min(4, zoom))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        current_color = pygame.Color(255, 255, 255)
                    if event.key == pygame.K_p:
                        current_color.hsva = (hue, sat, val, 100)

            keys = pygame.key.get_pressed()
            speed = 10 / zoom
            if keys[pygame.K_w]: camera_y -= speed
            if keys[pygame.K_s]: camera_y += speed
            if keys[pygame.K_a]: camera_x -= speed
            if keys[pygame.K_d]: camera_x += speed

            pixel_size = int(BASE_PIXEL_SIZE * zoom)

            if m_press[0]:
                if mx < 600 and my < 600:
                    gx = int((mx + camera_x) // pixel_size)
                    gy = int((my + camera_y) // pixel_size)
                    grid[(gx, gy)] = pygame.Color(current_color)

                elif 930 <= mx <= 960 and picker_y <= my <= picker_y + picker_size:
                    selector_hue[1] = max(picker_y, min(my, picker_y + picker_size))
                    hue = ((selector_hue[1] - picker_y) / picker_size) * 360
                    current_color.hsva = (hue, sat, val, 100)

                elif picker_x <= mx <= picker_x + picker_size and picker_y <= my <= picker_y + picker_size:
                    selector_sb[0] = max(picker_x, min(mx, picker_x + picker_size))
                    selector_sb[1] = max(picker_y, min(my, picker_y + picker_size))
                    sat = ((selector_sb[0] - picker_x) / picker_size) * 100
                    val = (1 - (selector_sb[1] - picker_y) / picker_size) * 100
                    current_color.hsva = (hue, sat, val, 100)

            cols = WIDTH // pixel_size + 2
            rows = HEIGHT // pixel_size + 2
            start_x = int(camera_x // pixel_size)
            start_y = int(camera_y // pixel_size)

            for x in range(start_x, start_x + cols):
                for y in range(start_y, start_y + rows):
                    sx = x * pixel_size - camera_x
                    sy = y * pixel_size - camera_y
                    color = grid.get((x, y), WHITE)
                    pygame.draw.rect(screen, color, (sx, sy, pixel_size, pixel_size))
                    pygame.draw.rect(screen, GRAY_LINE, (sx, sy, pixel_size, pixel_size), 1)

            for i in range(picker_size):
                c = pygame.Color(0)
                c.hsva = ((i / picker_size) * 360, 100, 100, 100)
                pygame.draw.line(screen, c, (930, picker_y + i), (960, picker_y + i))

            for x in range(0, 256, 4):
                for y in range(0, 256, 4):
                    c = pygame.Color(0)
                    c.hsva = (hue, (x / 255) * 100, (1 - y / 255) * 100, 100)
                    pygame.draw.rect(screen, c, (picker_x + x, picker_y + y, 4, 4))

            pygame.draw.circle(screen, WHITE, selector_sb, 6, 2)
            pygame.draw.circle(screen, WHITE, (945, selector_hue[1]), 6, 2)

            pygame.draw.rect(screen, current_color, (650, 320, 310, 50))
            screen.blit(
                font.render("WASD move | Mouse wheel zoom | E erase | P apply", True, BLACK),
                (650, 380)
            )

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def GUI():
        import tkinter as tk
        import random
        from PIL import Image, ImageTk
        import os

        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.configure(bg='lightblue')
        root.bind('<Escape>', lambda e: root.quit())

        bg_canvas = tk.Canvas(root, width=root.winfo_screenwidth(), 
                              height=root.winfo_screenheight(), 
                              bg='lightblue', highlightthickness=0)
        bg_canvas.place(x=0, y=0)

        shapes = []

        for i in range(20):
            x = random.randint(0, root.winfo_screenwidth())
            y = random.randint(0, root.winfo_screenheight())
            size = random.randint(20, 60)
            color = random.choice(['lightcoral', 'lightyellow', 'lightgreen', 'lavender'])
            
            shape_id = bg_canvas.create_oval(x, y, x+size, y+size, fill=color, outline='')
            
            dx = random.uniform(-1, 1)
            dy = random.uniform(-1, 1)
            
            shapes.append({'id': shape_id, 'x': x, 'y': y, 'dx': dx, 'dy': dy, 'size': size})

        def animate_shapes():
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            for shape in shapes:
                shape['x'] += shape['dx']
                shape['y'] += shape['dy']
                
                if shape['x'] < 0 or shape['x'] + shape['size'] > screen_width:
                    shape['dx'] = -shape['dx']
                if shape['y'] < 0 or shape['y'] + shape['size'] > screen_height:
                    shape['dy'] = -shape['dy']
                
                bg_canvas.coords(shape['id'], shape['x'], shape['y'], 
                                shape['x'] + shape['size'], shape['y'] + shape['size'])
            
            root.after(30, animate_shapes)

        center_container = tk.Frame(root, bg='lightblue')
        center_container.place(relx=0.5, rely=0.5, anchor='center')

        title = tk.Label(center_container, text="UP", font=('Arial', 65, 'bold'), 
                         bg='lightblue', fg='white')
        title.pack()

        canvas = tk.Canvas(center_container, width=200, height=200, bg='lightblue', 
                           highlightthickness=0)
        canvas.pack(pady=20)
        
        shadow = canvas.create_oval(10, 10, 190, 190, fill='gray20', outline='')
        circle = canvas.create_oval(5, 5, 185, 185, fill='yellow', outline='black', width=3)
        text = canvas.create_text(95, 95, text="START", font=('Arial', 28, 'bold'), 
                                 fill='black')

        def on_click(event):
            B127()

        canvas.bind('<Button-1>', on_click)

        pulse_growing = [True]
        current_size = [185]

        def animate_pulse():
            if pulse_growing[0]:
                current_size[0] += 1
                if current_size[0] >= 195:
                    pulse_growing[0] = False
            else:
                current_size[0] -= 1
                if current_size[0] <= 175:
                    pulse_growing[0] = True
            
            offset = (200 - current_size[0]) // 2
            shadow_offset = offset + 5
            
            canvas.coords(circle, offset, offset, offset + current_size[0], offset + current_size[0])
            canvas.coords(shadow, shadow_offset, shadow_offset, 
                          shadow_offset + current_size[0], shadow_offset + current_size[0])
            
            root.after(50, animate_pulse)

        animate_pulse()
        
        left_game_container = tk.Frame(root, bg='lightgreen')
        left_game_container.place(relx=0.15, rely=0.5, anchor='center')

        title_label = tk.Label(left_game_container, text="TIC TAC TOE", font=('Arial', 18, 'bold'), bg='lightgreen')
        title_label.grid(row=0, column=0, columnspan=4, pady=10)

        status_label = tk.Label(left_game_container, text="", font=('Arial', 14, 'bold'), bg='lightgreen')
        status_label.grid(row=1, column=0, padx=10)

        board_frame = tk.Frame(left_game_container, bg='lightgreen')
        board_frame.grid(row=1, column=1, columnspan=3)

        board_buttons = []
        for row in range(3):
            for col in range(3):
                btn = tk.Button(board_frame, text='', width=6, height=3, 
                               font=('Arial', 16, 'bold'), bg='grey')
                btn.grid(row=row, column=col, padx=2, pady=2)
                board_buttons.append(btn)
        
        board = [''] * 9
        game_over = [False]

        def reset_game():
            for i in range(9):
                board[i] = ''
                board_buttons[i].config(text='')
            status_label.config(text='')
            game_over[0] = False

        def make_move(index):
            if board[index] == '' and not game_over[0]:
                board[index] = 'X'
                board_buttons[index].config(text='X', fg='blue')
                
                if not check_winner():
                    bot_move()

        def bot_move():
            if game_over[0]:
                return
            empty_spots = [i for i in range(9) if board[i] == '']
            if empty_spots:
                choice = random.choice(empty_spots)
                board[choice] = 'O'
                board_buttons[choice].config(text='O', fg='red')
                check_winner()

        def check_winner():
            wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
            for a, b, c in wins:
                if board[a] == board[b] == board[c] != '':
                    game_over[0] = True
                    if board[a] == 'X':
                        status_label.config(text="W\nI\nN\nN\nE\nR", fg='green')
                    else:
                        status_label.config(text="L\nO\nS\nE\nR", fg='red')
                    root.after(2000, reset_game)
                    return True
            
            if '' not in board:
                game_over[0] = True
                status_label.config(text="T\nI\nE", fg='orange')
                root.after(2000, reset_game)
                return True
            
            return False

        for i in range(9):
            board_buttons[i].config(command=lambda idx=i: make_move(idx))

        race_canvas = tk.Canvas(root, width=80, height=80, bg='lightblue', highlightthickness=0)
        race_canvas.place(relx=0.98, rely=0.02, anchor='ne')

        gear_circle = race_canvas.create_oval(10, 10, 70, 70, fill='darkgray', outline='black', width=2)
        gear_inner = race_canvas.create_oval(25, 25, 55, 55, fill='gray', outline='black', width=2)

        teeth_positions = [
            (37, 5, 43, 15),  
            (55, 12, 68, 18),  
            (65, 37, 75, 43), 
            (55, 62, 68, 68),
            (37, 65, 43, 75), 
            (12, 62, 25, 68),
            (5, 37, 15, 43),
            (12, 12, 25, 18),
        ]
        
        for x1, y1, x2, y2 in teeth_positions:
            race_canvas.create_rectangle(x1, y1, x2, y2, fill='darkgray', outline='black', width=1)
        
        def on_race_click(event):
            race()
        
        race_canvas.bind('<Button-1>', on_race_click)
        

        def on_enter(event):
            race_canvas.itemconfig(gear_circle, fill='gray')
            race_canvas.itemconfig(gear_inner, fill='lightgray')
            for x1, y1, x2, y2 in teeth_positions:
                items = race_canvas.find_overlapping(x1, y1, x2, y2)
                for item in items:
                    if race_canvas.type(item) == 'rectangle':
                        race_canvas.itemconfig(item, fill='gray')
        
        def on_leave(event):
            race_canvas.itemconfig(gear_circle, fill='darkgray')
            race_canvas.itemconfig(gear_inner, fill='gray')
            items = race_canvas.find_all()
            for item in items:
                if race_canvas.type(item) == 'rectangle':
                    race_canvas.itemconfig(item, fill='darkgray')
        
        race_canvas.bind('<Enter>', on_enter)
        race_canvas.bind('<Leave>', on_leave)

        marker_button_container = tk.Label(root, bg='lightblue')
        marker_button_container.place(relx=0.5, rely=0.88, anchor='center')

        try:
            BASE_DIR = os.path.dirname(__file__)
            IMG_DIR = os.path.join(BASE_DIR, "images")
            marker_path = os.path.join(IMG_DIR, "marker.png")
            marker_img = Image.open(marker_path)
            marker_img = marker_img.resize((120, 120), Image.Resampling.LANCZOS)
            marker_photo = ImageTk.PhotoImage(marker_img)
            
            marker_label = tk.Label(marker_button_container, image=marker_photo, bg='lightblue', cursor='hand2')
            marker_label.image = marker_photo
            marker_label.pack()
            
            def on_marker_click(event):
                pixel()
            
            marker_label.bind('<Button-1>', on_marker_click)
            
        except Exception as e:
            fallback_button = tk.Button(marker_button_container, text="PIXEL ART", 
                                       font=('Arial', 16, 'bold'), 
                                       bg='purple', fg='white',
                                       command=pixel,
                                       width=12, height=2)
            fallback_button.pack()

        right_game = tk.Frame(root, bg='lightgreen', width=300, height=300)
        right_game.place(relx=0.85, rely=.5, anchor='center')

        rhythm_canvas = tk.Canvas(right_game, width=300, height=400, bg='lightgreen')
        rhythm_canvas.pack()

        target_y = 350
        rhythm_canvas.create_rectangle(50, target_y-20, 250, target_y+20, outline='black', width=3)
        rhythm_canvas.create_text(150, target_y, text="HIT ZONE", font=('Arial', 12, 'bold'))
        
        arrows = []
        arrow_directions = ['Left', 'Up', 'Down', 'Right']
        arrow_symbols = {'Left': '←', 'Up': '↑', 'Down': '↓', 'Right': '→'}
        
        score = [0]
        score_label = tk.Label(right_game, text="Score: 0", font=('Arial', 16, 'bold'), bg='lightgreen')
        score_label.pack()

        def create_arrow():
            direction = random.choice(arrow_directions)
        
            lane_positions = {'Left': 75, 'Up': 125, 'Down': 175, 'Right': 225}
            x = lane_positions[direction]
            y = 0

            arrow_id = rhythm_canvas.create_text(x, y, text=arrow_symbols[direction], 
                                         font=('Arial', 40, 'bold'), fill='blue')

            arrows.append({'id': arrow_id, 'direction': direction, 'y': y, 'x': x})
        
        spawn_timer = [0]

        def update_arrows():
            for arrow in arrows[:]:
                arrow['y'] += 3
                rhythm_canvas.coords(arrow['id'], arrow['x'], arrow['y'])
            
                if arrow['y'] > 400:
                    score[0] -= 5
                    score_label.config(text=f"Score: {score[0]}")
                    rhythm_canvas.delete(arrow['id'])
                    arrows.remove(arrow)
        
            spawn_timer[0] += 1
            if spawn_timer[0] >= 60:
                create_arrow()
                spawn_timer[0] = 0
        
            root.after(30, update_arrows)

        def check_hit(key_pressed):
            hit_range = 30
        
            for arrow in arrows[:]:
                if arrow['direction'] == key_pressed:
                    distance = abs(arrow['y'] - target_y)
                
                    if distance < hit_range:
                        score[0] += 10
                        score_label.config(text=f"Score: {score[0]}")
                        rhythm_canvas.delete(arrow['id'])
                        arrows.remove(arrow)
                        return

        def on_key_press(event):
            check_hit(event.keysym)

        root.bind('<Left>', on_key_press)
        root.bind('<Up>', on_key_press)
        root.bind('<Down>', on_key_press)
        root.bind('<Right>', on_key_press)
        
        animate_shapes()
        create_arrow()
        update_arrows()

        root.mainloop()
    GUI()          
game1()