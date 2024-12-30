import this

import pyxel
import random


class Entity:
    def __init__(self, x, y, width, height, color=11, frame_color=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.frame_color = frame_color or color

    def draw(self):
        if self.frame_color:
            pyxel.rectb(self.x, self.y, self.width, self.height, self.frame_color)
        pyxel.rect(self.x, self.y, self.width, self.height, self.color)

    def is_colliding(self, x, y, width, height):
        return (
                x < self.x + self.width
                and x + width > self.x
                and y < self.y + self.height
                and y + height > self.y
        )


class Player(Entity):
    def __init__(self, x, y, width, height, color=11):
        super().__init__(x, y, width, height, color)
        self.vx = 0.0
        self.vy = 0.0
        self.life = 3
        self.gravity = 0.5
        self.jump_strength = -5.0
        self.move_speed = 2.0
        self.on_ground = False

    def update(self, blocks):
        self.vx = 0.0
        if pyxel.btn(pyxel.KEY_LEFT):
            self.vx = -self.move_speed
        elif pyxel.btn(pyxel.KEY_RIGHT):
            self.vx = self.move_speed
        if pyxel.btnp(pyxel.KEY_SPACE) and self.on_ground:
            self.vy = self.jump_strength

        self.vy += self.gravity
        next_x = self.x + self.vx
        next_y = self.y + self.vy

        next_x, next_y = self.handle_collisions(next_x, next_y, blocks)

        self.x = next_x
        self.y = next_y

        self.on_ground = self.check_on_ground(blocks)

    def handle_collisions(self, next_x, next_y, blocks):
        for block in blocks:
            if block.is_colliding(next_x, self.y, self.width, self.height):
                if self.vx > 0:
                    next_x = block.x - self.width
                elif self.vx < 0:
                    next_x = block.x + block.width
                self.vx = 0
            if block.is_colliding(self.x, next_y, self.width, self.height):
                if self.vy > 0:
                    next_y = block.y - self.height
                elif self.vy < 0:
                    next_y = block.y + block.height
                self.vy = 0
        return next_x, next_y

    def check_on_ground(self, blocks):
        for block in blocks:
            if block.is_colliding(self.x, self.y + 1, self.width, self.height):
                return True
        return False

    def draw(self):
        pyxel.rect(self.x, self.y, self.width, self.height, self.color)


class Mob(Entity):
    def __init__(self, x, y, width, height, color=8):
        super().__init__(x, y, width, height, color)
        self.vx = 1

    def update(self, blocks):
        next_x = self.x + self.vx
        collision = False
        for block in blocks:
            if block.is_colliding(next_x, self.y, self.width, self.height):
                collision = True
                break
        if collision:
            self.vx = -self.vx
        else:
            self.x = next_x


class PowerUp(Entity):
    def __init__(self, x, y, width, height, color=10, effect=None):
        super().__init__(x, y, width, height, color)
        self.effect = effect

    def apply(self, player):
        if self.effect == "speed":
            player.move_speed += 0.5
        elif self.effect == "jump":
            player.jump_strength *= 1.2
        elif self.effect == "invincibility":
            player.invincibility_timer = pyxel.frame_count + 300


class Collectible(Entity):
    def __init__(self, x, y, width, height, color=14):
        super().__init__(x, y, width, height, color)

    def collect(self, player):
        player.vy = -10  # 27ジャンプ
        player.life += 1  # プレイヤーのライフを増やす


class PlatformerGame:
    def __init__(self):
        pyxel.init(160, 120, title="Platformer Game", fps=30)
        self.state = "TITLE"
        self.level = 1
        self.score = 0
        self.life = 3
        self.player = Player(20, 80, 8, 8)
        self.mobs = []
        self.blocks = []
        self.powerups = []
        self.collectibles = []
        self.entities = [self.player]

        self.generate_entities()

        pyxel.run(self.update, self.draw)

    def generate_entities(self):
        ground_y = 100
        self.blocks.append(Entity(0, ground_y, 160, 20, color=3, frame_color=7))
        for i in range(10):
            x = random.randint(50, 300)
            y = random.randint(ground_y - 40, ground_y - 10)
            self.blocks.append(Entity(x, y, 20, 10, color=3, frame_color=7))
            self.mobs.append(Mob(x + 20, y - 10, 8, 8))
            if random.random() < 0.5:
                self.powerups.append(
                    PowerUp(x + 10, y - 20, 8, 8, effect=random.choice(["speed", "jump", "invincibility"])))
            else:
                self.collectibles.append(Collectible(x + 10, y - 20, 8, 8))

        self.entities.extend(self.blocks + self.mobs + self.powerups + self.collectibles)

    def update(self):
        if self.player.y > pyxel.height * 2:  # y座標が大きい場合、ゲームオーバー
            self.state = "GAME_OVER"
        if self.state == "TITLE":
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.state = "PLAY"
        elif self.state == "PLAY":
            self.update_game()
            if self.life <= 0:
                self.state = "GAME_OVER"
        elif self.state == "GAME_OVER":
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset_game()

    def update_game(self):
        self.player.update(self.blocks)
        for mob in self.mobs:
            mob.update(self.blocks)
            if self.player.is_colliding(mob.x, mob.y, mob.width, mob.height):
                #if self.player.invincibility_timer < pyxel.frame_count:
                #    self.life -= 1
                self.mobs.remove(mob)
                break
        for powerup in self.powerups[:]:
            if self.player.is_colliding(powerup.x, powerup.y, powerup.width, powerup.height):
                powerup.apply(self.player)
                self.powerups.remove(powerup)
                self.score += 100

        for collectible in self.collectibles[:]:
            if self.player.is_colliding(collectible.x, collectible.y, collectible.width, collectible.height):
                collectible.collect(self.player)
                self.collectibles.remove(collectible)

    def reset_game(self):
        self.score = 0
        self.life = 3
        self.level = 1
        self.player = Player(20, 80, 8, 8)
        self.mobs = []
        self.blocks = []
        self.powerups = []
        self.collectibles = []
        self.entities = [self.player]

        self.generate_entities()
        self.state = "TITLE"

    def draw(self):
        pyxel.cls(0)

        # カメラ設定: プレイヤーを画面中心に配置
        camera_x = self.player.x - (pyxel.width // 2) + (self.player.width // 2)
        camera_y = self.player.y - (pyxel.height // 2) + (self.player.height // 2)
        pyxel.camera(camera_x, camera_y)

        if self.state == "TITLE":
            pyxel.text(camera_x + 50, camera_y + 50, "Well Came to Game", pyxel.COLOR_RED)
            pyxel.text(camera_x + 40, camera_y + 60, "Press RETURN to Start", pyxel.COLOR_WHITE)
        elif self.state == "PLAY":
            for entity in self.entities:
                entity.draw()
            pyxel.text(camera_x + 5, camera_y + 5, f"Score: {self.score}", pyxel.COLOR_WHITE)
            pyxel.text(camera_x + 5, camera_y + 15, f"Life: {self.life}", pyxel.COLOR_RED)
            pyxel.text(camera_x + 5, camera_y + 25, f"Level: {self.level}", pyxel.COLOR_GREEN)
            pyxel.text(camera_x + 5, camera_y + 35, f"Posion: {float(self.player.x)} : {float(-self.player.y)}",
                       pyxel.COLOR_YELLOW)
            pyxel.text(camera_x + 5, camera_y + 55, f"Developer:", pyxel.COLOR_DARK_BLUE)
            pyxel.text(camera_x + 5, camera_y + 65, f"on_ground: {self.player.on_ground}", pyxel.COLOR_DARK_BLUE)
            pyxel.text(camera_x + 5, camera_y + 75, f"color: {self.player.color}", pyxel.COLOR_DARK_BLUE)
        elif self.state == "GAME_OVER":
            pyxel.text(camera_x + 50, camera_y + 50, "GAME OVER", pyxel.COLOR_RED)
            pyxel.text(camera_x + 40, camera_y + 60, "Press RETURN to Restart", pyxel.COLOR_WHITE)

PlatformerGame()
