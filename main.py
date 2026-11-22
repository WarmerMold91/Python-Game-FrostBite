#William
#Start Date: 11/19/2026
#Top down Survival Game based on dead town, with Mechcanics from the long dark.
#V0.1

import math
import random
import sys
import pygame

# --- INITIALIZATION ---
pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FrostBite - 2D Survival Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 18)
large_font = pygame.font.SysFont("consolas", 36, bold=True)

# --- COLORS ---
SNOW_DAY = (210, 225, 235)
SNOW_NIGHT = (40, 55, 75)
PLAYER_COLOR = (50, 120, 200)
FIRE_COLOR = (255, 120, 20)
FIRE_GLOW = (255, 200, 80)
TREE_COLOR = (35, 85, 50)
LOOT_COLOR = (180, 130, 70)
UI_BG = (20, 25, 30)
WHITE = (255, 255, 255)
RED = (220, 60, 60)
BLUE = (70, 170, 255)
ORANGE = (240, 150, 50)
GREEN = (80, 200, 100)


class Player:

  def __init__(self, x, y):
    self.pos = pygame.Vector2(x, y)
    self.speed = 200  # pixels per second
    self.radius = 16
    self.angle = 0

    # The Long Dark Survival Meters (0 to 100)
    self.health = 100.0
    self.warmth = 85.0
    self.calories = 80.0
    self.hydration = 80.0

    # Dead Town Style Inventory
    self.inventory = {"wood": 2, "food": 1, "water": 1}

  def update(self, dt, keys, mouse_pos, ambient_temp, campfires):
    # Movement (WASD)
    move = pygame.Vector2(0, 0)
    if keys[pygame.K_w]:
      move.y -= 1
    if keys[pygame.K_s]:
      move.y += 1
    if keys[pygame.K_a]:
      move.x -= 1
    if keys[pygame.K_d]:
      move.x += 1

    if move.length() > 0:
      move = move.normalize() * self.speed * dt
      self.pos += move

    # Keep player inside screen bounds
    self.pos.x = max(self.radius, min(WIDTH - self.radius, self.pos.x))
    self.pos.y = max(self.radius, min(HEIGHT - 100 - self.radius, self.pos.y))

    # Aim towards mouse cursor (Dead Town top-down look)
    dx = mouse_pos[0] - self.pos.x
    dy = mouse_pos[1] - self.pos.y
    self.angle = math.atan2(dy, dx)

    # Check if near a warm campfire
    near_fire = False
    for fire in campfires:
      if self.pos.distance_to(fire["pos"]) < 110:
        near_fire = True
        break

    # Survival Stat Decay & Recovery
    self.calories = max(0.0, self.calories - 1.2 * dt)
    self.hydration = max(0.0, self.hydration - 1.8 * dt)

    if near_fire:
      self.warmth = min(100.0, self.warmth + 12.0 * dt)
    else:
      # Colder ambient temperatures drain warmth faster
      cold_drain = max(0.5, (15 - ambient_temp) * 0.15)
      self.warmth = max(0.0, self.warmth - cold_drain * dt)

    # Health damage if any core need hits zero
    if self.warmth <= 0:
      self.health -= 4.0 * dt
    if self.calories <= 0:
      self.health -= 2.0 * dt
    if self.hydration <= 0:
      self.health -= 3.5 * dt

    # Slow health regen if well-fed, hydrated, and warm
    if (
        self.warmth > 50
        and self.calories > 50
        and self.hydration > 50
        and self.health < 100
    ):
      self.health = min(100.0, self.health + 1.5 * dt)

  def draw(self, surface):
    # Draw player body
    pygame.draw.circle(
        surface, PLAYER_COLOR, (int(self.pos.x), int(self.pos.y)), self.radius
    )
    # Draw directional pointer (flashlight / weapon facing)
    end_x = self.pos.x + math.cos(self.angle) * 24
    end_y = self.pos.y + math.sin(self.angle) * 24
    pygame.draw.line(surface, WHITE, self.pos, (end_x, end_y), 4)


def spawn_loot(count=12):
  items = []
  types = ["wood", "food", "water"]
  for _ in range(count):
    x = random.randint(40, WIDTH - 40)
    y = random.randint(40, HEIGHT - 140)
    items.append({"pos": pygame.Vector2(x, y), "type": random.choice(types)})
  return items


def draw_bar(surface, x, y, width, height, value, color, label):
  pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
  fill_w = int((value / 100.0) * width)
  pygame.draw.rect(surface, color, (x, y, fill_w, height))
  pygame.draw.rect(surface, WHITE, (x, y, width, height), 1)
  text = font.render(f"{label}: {int(value)}%", True, WHITE)
  surface.blit(text, (x + 6, y + 2))


def main():
  player = Player(WIDTH // 2, (HEIGHT - 100) // 2)
  loot_items = spawn_loot(14)
  campfires = []
  game_time = 0.0  # Seconds elapsed (60s = 1 full day/night cycle)
  loot_respawn_timer = 0.0
  game_over = False

  while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
        sys.exit()

      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()

        if not game_over:
          # [1] Eat Food
          if event.key == pygame.K_1 and player.inventory["food"] > 0:
            player.inventory["food"] -= 1
            player.calories = min(100.0, player.calories + 35.0)
          # [2] Drink Water
          elif event.key == pygame.K_2 and player.inventory["water"] > 0:
            player.inventory["water"] -= 1
            player.hydration = min(100.0, player.hydration + 40.0)
          # [3] Build Campfire (Costs 2 Wood)
          elif event.key == pygame.K_3 and player.inventory["wood"] >= 2:
            player.inventory["wood"] -= 2
            campfires.append({"pos": player.pos.copy(), "fuel": 25.0})
        else:
          # Restart on R
          if event.key == pygame.K_r:
            main()
            return

    if not game_over:
      game_time += dt
      loot_respawn_timer += dt

      # Day/Night & Temperature Cycle (60 sec cycle)
      cycle = (game_time % 60.0) / 60.0  # 0.0 to 1.0
      is_night = cycle > 0.5
      ambient_temp = -18 if is_night else -2

      # Respawn scavenging nodes periodically
      if loot_respawn_timer > 15.0 and len(loot_items) < 12:
        loot_items.extend(spawn_loot(4))
        loot_respawn_timer = 0.0

      # Update campfires
      for fire in campfires[:]:
        fire["fuel"] -= dt
        if fire["fuel"] <= 0:
          campfires.remove(fire)

      # Update Player
      keys = pygame.key.get_pressed()
      player.update(dt, keys, mouse_pos, ambient_temp, campfires)

      # Scavenging collision
      for item in loot_items[:]:
        if player.pos.distance_to(item["pos"]) < player.radius + 12:
          player.inventory[item["type"]] += 1
          loot_items.remove(item)

      if player.health <= 0:
        game_over = True

    # --- RENDERING ---
    bg_color = SNOW_NIGHT if (game_time % 60.0) > 30.0 else SNOW_DAY
    screen.fill(bg_color)

    # Draw Campfires & Warmth Radius
    for fire in campfires:
      pos = (int(fire["pos"].x), int(fire["pos"].y))
      pygame.draw.circle(screen, FIRE_GLOW, pos, 110, 2)
      pygame.draw.circle(screen, FIRE_COLOR, pos, 14)

    # Draw Scavenging Nodes
    for item in loot_items:
      pos = (int(item["pos"].x), int(item["pos"].y))
      pygame.draw.rect(screen, LOOT_COLOR, (pos[0] - 8, pos[1] - 8, 16, 16))
      tag = font.render(item["type"][0].upper(), True, WHITE)
      screen.blit(tag, (pos[0] - 5, pos[1] - 9))

    # Draw Player
    player.draw(screen)

    # --- BOTTOM HUD PANEL ---
    pygame.draw.rect(screen, UI_BG, (0, HEIGHT - 100, WIDTH, 100))
    draw_bar(screen, 20, HEIGHT - 85, 180, 24, player.health, RED, "Health")
    draw_bar(screen, 20, HEIGHT - 45, 180, 24, player.warmth, BLUE, "Warmth")
    draw_bar(
        screen, 220, HEIGHT - 85, 180, 24, player.calories, ORANGE, "Calories"
    )
    draw_bar(
        screen, 220, HEIGHT - 45, 180, 24, player.hydration, GREEN, "Hydration"
    )

    # Inventory & Controls Display
    inv_text = font.render(
        f"Inventory -> Wood: {player.inventory['wood']} | Food:"
        f" {player.inventory['food']} | Water: {player.inventory['water']}",
        True,
        WHITE,
    )
    ctrl_text = font.render(
        "[WASD] Move  [1] Eat Food  [2] Drink Water  [3] Build Fire (2 Wood)",
        True,
        (180, 200, 220),
    )

    time_label = "NIGHT (-18°C)" if (game_time % 60.0) > 30.0 else "DAY (-2°C)"
    env_text = font.render(
        f"Survived: {int(game_time)}s | {time_label}", True, FIRE_GLOW
    )

    screen.blit(inv_text, (430, HEIGHT - 85))
    screen.blit(ctrl_text, (430, HEIGHT - 58))
    screen.blit(env_text, (430, HEIGHT - 30))

    if game_over:
      overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
      overlay.fill((0, 0, 0, 180))
      screen.blit(overlay, (0, 0))
      msg = large_font.render(
          f"YOU FROZE OR STARVED - Survived {int(game_time)}s", True, RED
      )
      sub = font.render("Press [R] to Restart or [ESC] to Quit", True, WHITE)
      screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 30))
      screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))

    pygame.display.flip()


if __name__ == "__main__":
  main()