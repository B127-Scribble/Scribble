import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 950, 700
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Endless War: Scaling Economy")

FONT_S = pygame.font.SysFont('Consolas', 14)
FONT_M = pygame.font.SysFont('Segoe UI', 19, bold=True)

BG, PANEL = (10, 12, 18), (25, 27, 38)
ACCENT_BLUE, ACCENT_RED, ACCENT_GREEN = (0, 160, 255), (255, 70, 70), (50, 230, 50)
TEXT, GOLD, FOG = (220, 220, 220), (255, 200, 0), (5, 5, 10)

class InfiniteWar:
    def __init__(self):
        self.cell_size = 50
        self.owned_coords = [(0, 0)]
        self.defenses = {(0, 0): 1}
        self.seen_coords = set([(0,0), (1,0), (-1,0), (0,1), (0,-1)])
        self.selected_coord = (0, 0)
        self.cam_x, self.cam_y = -200, -200
        
        self.resources, self.army, self.enemy_strength = 100, 20, 10
        self.army_purchases = 0 
        
        self.gather_buffer = 0 
        self.gather_max = 400 
        self.pending_resources = 0
        
        self.update_vision()

    def update_vision(self):
        for cx, cy in self.owned_coords:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    self.seen_coords.add((cx + dx, cy + dy))

    def add_log(self, msg, color=TEXT):
        self.logs = getattr(self, 'logs', [])
        self.logs.append((f"> {msg}", color))
        if len(self.logs) > 6: self.logs.pop(0)

    def draw(self):
        WIN.fill(BG)
        map_clip = pygame.Rect(30, 30, 450, 450)
        pygame.draw.rect(WIN, PANEL, map_clip, border_radius=15)
        
        s_col, s_row = (self.cam_x // 50) - 1, (self.cam_y // 50) - 1
        for r in range(int(s_row), int(s_row + 12)):
            for c in range(int(s_col), int(s_col + 12)):
                rx, ry = 30 + (c * 50) - self.cam_x, 30 + (r * 50) - self.cam_y
                rect = pygame.Rect(rx + 2, ry + 2, 46, 46)
                if not map_clip.colliderect(rect): continue
                coord = (c, r)
                if coord not in self.seen_coords:
                    pygame.draw.rect(WIN, FOG, rect, border_radius=6)
                else:
                    color = GOLD if coord == self.selected_coord else (ACCENT_BLUE if coord in self.owned_coords else (40, 42, 55))
                    pygame.draw.rect(WIN, color, rect, border_radius=6)
                    if coord in self.defenses:
                        lvl = FONT_S.render(str(self.defenses[coord]), True, BG)
                        WIN.blit(lvl, (rect.centerx-4, rect.centery-7))

        attack_cost = len(self.owned_coords) * 20
        army_cost = 20 + (self.army_purchases * 10)
        def_cost = self.defenses.get(self.selected_coord, 1) * 25 if self.selected_coord in self.owned_coords else 0

        stats = [
            (f"RESOURCES: {self.resources}", GOLD), 
            (f"ARMY: {self.army}", TEXT), 
            (f"LANDS: {len(self.owned_coords)}", ACCENT_BLUE), 
            (f"ENEMY POWER: {self.enemy_strength}", ACCENT_RED),
        ]
        for i, (txt, col) in enumerate(stats): WIN.blit(FONT_M.render(txt, True, col), (540, 50 + i*35))

        self.btns = [
            (f"ATTACK NEIGHBOR (-{attack_cost})", 280, lambda: self.logic_attack(attack_cost)),
            (f"UPGRADE LAND (-{def_cost})", 340, lambda: self.logic_upgrade(def_cost)),
            (f"BUILD ARMY (-{army_cost})", 400, lambda: self.logic_build(army_cost)),
            (f"COLLECT (+{self.pending_resources})", 530, self.logic_collect)
        ]
        
        mx, my = pygame.mouse.get_pos()
        for txt, y, func in self.btns:
            rect = pygame.Rect(530, y, 380, 50)
            btn_col = (70, 75, 100) if rect.collidepoint(mx, my) else (40, 43, 60)
            pygame.draw.rect(WIN, btn_col, rect, border_radius=8)
            WIN.blit(FONT_M.render(txt, True, TEXT), (rect.centerx - 120, rect.y + 12))

        pygame.draw.rect(WIN, (30, 30, 40), (530, 490, 380, 15), border_radius=5)
        fill_w = (self.gather_buffer / self.gather_max) * 380
        pygame.draw.rect(WIN, ACCENT_GREEN, (530, 490, fill_w, 15), border_radius=5)

        pygame.draw.rect(WIN, PANEL, (30, 530, 450, 140), border_radius=15)
        for i, (msg, col) in enumerate(getattr(self, 'logs', [])): WIN.blit(FONT_S.render(msg, True, col), (45, 545 + i*20))
        pygame.display.flip()

    def update_logic(self):
        self.gather_buffer += 0.2 + (len(self.owned_coords) * 0.05)
        if self.gather_buffer >= self.gather_max:
            self.gather_buffer = 0
            self.pending_resources += len(self.owned_coords) * 5
        if random.random() < 0.0005: self.check_enemy_raid()

    def logic_collect(self):
        if self.pending_resources > 0:
            self.resources += self.pending_resources
            self.add_log(f"Collected {self.pending_resources} resources.", GOLD)
            self.pending_resources = 0

    def handle_scroll(self):
        keys = pygame.key.get_pressed()
        speed = 7
        if keys[pygame.K_LEFT]: self.cam_x -= speed
        if keys[pygame.K_RIGHT]: self.cam_x += speed
        if keys[pygame.K_UP]: self.cam_y -= speed
        if keys[pygame.K_DOWN]: self.cam_y += speed

    def handle_click(self, pos):
        mx, my = pos
        if 30 <= mx <= 480 and 30 <= my <= 480:
            self.selected_coord = (int((mx - 30 + self.cam_x) // 50), int((my - 30 + self.cam_y) // 50))
        for txt, y, func in self.btns:
            if 530 <= mx <= 910 and y <= my <= y+50: func()

    def check_enemy_raid(self):
        t = random.choice(self.owned_coords)
        if self.enemy_strength + random.randint(0, 15) > self.defenses[t] * 10:
            self.defenses[t] = max(1, self.defenses[t] - 1)
            self.add_log(f"RAID: {t} damaged!", ACCENT_RED)
        else: self.add_log(f"RAID: Repelled at {t}.", ACCENT_GREEN)

    def logic_attack(self, cost):
        if self.resources < cost:
            self.add_log("Need more resources to launch attack!", ACCENT_RED)
            return
        if self.selected_coord in self.owned_coords: return
        cx, cy = self.selected_coord
        if not any(n in self.owned_coords for n in [(cx+1,cy), (cx-1,cy), (cx,cy+1), (cx,cy-1)]):
            self.add_log("Attack only adjacent lands!", ACCENT_RED)
            return
        
        self.resources -= cost
        if self.army + random.randint(0, 10) > self.enemy_strength + random.randint(5, 20):
            self.owned_coords.append(self.selected_coord)
            self.defenses[self.selected_coord] = 1
            self.enemy_strength += 2
            self.update_vision()
            self.add_log(f"Captured {self.selected_coord}!", ACCENT_GREEN)
        else:
            loss = random.randint(3, 7)
            self.army = max(0, self.army - loss)
            self.add_log(f"Defeat! Lost {loss} army.", ACCENT_RED)
        if self.army <= 0: pygame.quit(); sys.exit()

    def logic_upgrade(self, cost):
        if self.selected_coord not in self.owned_coords: return
        if self.resources >= cost:
            self.resources -= cost
            self.defenses[self.selected_coord] += 1
            self.add_log(f"Upgraded to Lv.{self.defenses[self.selected_coord]}", ACCENT_BLUE)
        else: self.add_log("Insufficient funds for upgrade.", ACCENT_RED)

    def logic_build(self, cost):
        if self.resources >= cost:
            self.resources -= cost
            self.army += 10
            self.army_purchases += 1
            self.add_log("Reinforcements deployed.", TEXT)
        else: self.add_log("Cannot afford more soldiers.", ACCENT_RED)

game, clock = InfiniteWar(), pygame.time.Clock()
while True:
    game.handle_scroll()
    game.update_logic()
    game.draw()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN: game.handle_click(pygame.mouse.get_pos())
    clock.tick(60)
