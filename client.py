import pygame, math, time, random
from pygame import mixer
from network import Network
from settings import *


# Init and Create Window
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()
pygame.display.set_caption(WINDOW_TITLE)
pygame.display.set_icon(pygame.image.load('menu/yoshi.png'))
pygame.mouse.set_cursor(pygame.cursors.broken_x)

# Variables
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock() #For getting fps
main_menu = True
game_over = False
prev_time = time.time() # Ensure Game Consistency If Lag
dt = 0

# Load and Size Images
right = [None]*6 #Sprite frames
left = [None]*6
stationaryR = [None]*4
stationaryL = [None]*4
for picIndex in range(1,7):
    right[picIndex-1] = pygame.image.load('character/run' + str(picIndex) + '.png')
    left[picIndex-1] = pygame.transform.flip(right[picIndex-1], True, False)
for picIndex in range(1,5):
    stationaryR[picIndex-1] = pygame.image.load('character/idle' + str(picIndex) + '.png')
    stationaryL[picIndex-1] = pygame.transform.flip(stationaryR[picIndex-1], True, False)
menu_img = pygame.transform.scale(pygame.image.load('menu/menu_img.png'), (SCREEN_WIDTH, SCREEN_HEIGHT))
restart_img = pygame.transform.scale(pygame.image.load('menu/restart_button.png'), (130, 80))
start_img = pygame.transform.scale(pygame.image.load('menu/start_button.png'), (130, 80))
exit_img = pygame.transform.scale(pygame.image.load('menu/exit_button.png'), (130, 80))
title_img = pygame.image.load('menu/title.png')
background_img = pygame.transform.scale(pygame.image.load('map/map1.jpg'), (SCREEN_WIDTH, SCREEN_HEIGHT))
bullet_img = pygame.transform.scale(pygame.image.load('specialfx/bullet.png'), (30, 22))

# Load and Equalize Sounds
shoot_fx = pygame.mixer.Sound('specialfx/shoot_sound.wav')
shoot_fx.set_volume(VOLUME - 0.16)
death_fx = pygame.mixer.Sound('specialfx/death_sound.wav')
death_fx.set_volume(VOLUME - 0.1)
#walk_fx = 
damage_fx = pygame.mixer.Sound('specialfx/damage_sound.wav')
damage_fx.set_volume(VOLUME)
#sword_fx = 
jump_fx = pygame.mixer.Sound('specialfx/jump_sound.wav')
jump_fx.set_volume(VOLUME - 0.1)
menu_fx = pygame.mixer.Sound('specialfx/click_sound.wav')
menu_fx.set_volume(VOLUME + 0.1)

# Draw Text Function
font_fps = pygame.font.SysFont('Arial', 18)
font_health = pygame.font.SysFont('Futura', 90)
def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# Timer Function
def timer(var, timer): # Set a variable to 1 then use this function, it will start a timer
    if var >= timer: # Timer is length of cooldown
        var = 0
    elif var > 0:
        var += 1
    return var

class World():
    def __init__(self, data):
        self.tile_list = []
        # Load Map Images
        floor_img = pygame.image.load('map/floor.png')
        # Append Images/Rectangles to tile_list
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row: #Here, each number after == represents a specific block type to be put on the map
                if tile == 1:
                    img = pygame.transform.scale(floor_img, (TILE_SIZE, TILE_SIZE))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * TILE_SIZE
                    img_rect.y = row_count * TILE_SIZE
                    tile = (img, img_rect) #Tile[0] is sprite image, tile[1] is physical rectangle on grid
                    self.tile_list.append(tile)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            # Hitboxes
            if SHOW_HITBOX:
                pygame.draw.rect(screen, (255,255,255), tile[1], 5)
            # Draw Sprite Image
            screen.blit(tile[0], tile[1])

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        pygame.draw.rect(screen, (230,70,50), self.rect)
        # Mouse pos
        pos = pygame.mouse.get_pos()
        # Mouse Hovering Over Button
        if self.rect.collidepoint(pos):
            # Change rectangle color
            pygame.draw.rect(screen, (183,53,37), self.rect)
            # Check for clicks
            if pygame.mouse.get_pressed()[0] and self.clicked == False:
                menu_fx.play()
                self.clicked = True
                time.sleep(0.2) #Fixes bug where you attack after pressing button
            if pygame.mouse.get_pressed()[0] == False:
                self.clicked = False
        # Draw Button
        screen.blit(self.image, self.rect)

class Player():
    def __init__(self, x, y):
        self.reset(x, y) #For reinitializing player when you restart game
        
    def move(self, userInput):
        self.dy = 0
        # Jump
        if (userInput[pygame.K_w] or userInput[pygame.K_SPACE]) and not self.jumped and self.invincibility_timer == 0:
            jump_fx.play()
            self.vel_y = -19 #Jump height
            self.jumped = True
        # Gravity
        self.vel_y += 1.1 #Fall speed
        if self.vel_y > 25: #Terminal velocity
            self.vel_y = 25
        self.dy += self.vel_y
        # Walk
        if userInput[pygame.K_d] and not self.jumped and self.invincibility_timer == 0:
            self.dx += 1 #Walk acceleration
            if self.dx >= 8: #Max walk speed
                self.dx = 8
            self.face_right = True
            self.face_left = False
        elif userInput[pygame.K_a] and not self.jumped and self.invincibility_timer == 0:
            self.dx -= 1
            if self.dx <= -8:
                self.dx = -8
            self.face_right = False
            self.face_left = True
        # Keep Aerial Momentum
        elif self.stored_direction and self.jumped and self.dx != 0: 
            self.dx = 13 #Aerial speed
        elif not(self.stored_direction) and self.jumped and self.dx != 0:
            self.dx = -13
        # Finally
        else:
            if self.dx > 0: #Decelerate walk
                self.dx -= 1
            elif self.dx < 0:
                self.dx += 1
            self.face_right = False
            self.face_left = False     
        # Collision in y Direction
        for tile in world.tile_list: 
            if tile[1].colliderect(self.hitbox.x, self.hitbox.y + self.dy, self.hitbox.width, self.hitbox.height):
                if self.vel_y < 0: #If hitting head
                    self.dy = tile[1].bottom - self.hitbox.top
                    self.vel_y = 0
                elif self.vel_y >= 0: #If hitting floor
                    self.dy = tile[1].top - self.hitbox.bottom
                    self.vel_y = 0
                    self.jumped = False
        # Collision in x Direction
            if tile[1].colliderect(self.hitbox.x + self.dx, self.hitbox.y, self.hitbox.width, self.hitbox.height):
                self.dx = 0
        # Update Movement (must be here)
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        # Hitbox
        self.hitbox = pygame.Rect(self.x + 60, self.y + 30, 40, 80) # Constants: xpos and ypos of hitbox, width and height of hitbox
        if SHOW_HITBOX:
            pygame.draw.rect(screen, (0,0,0), self.hitbox, 1)
        #Sprite Animation
        if self.stepIndex >= 60: #This step index is a multiple of the amount of frames in the sprite to slow the sprite
            self.stepIndex = 0
        if self.face_right:
            screen.blit(right[self.stepIndex//10], (self.x, self.y)) #stepIndex divided by this number must be equal to the amount of frames the animation has
            self.stored_direction = True
            self.stepIndex += 1
        if self.face_left:
            screen.blit(left[self.stepIndex//10], (self.x, self.y))
            self.stored_direction = False
            self.stepIndex += 1
        if not self.face_left and not self.face_right:
            if self.stepIndex >= 56:
                self.stepIndex = 0
            if self.stored_direction == True:
                screen.blit(stationaryR[self.stepIndex//14], (self.x, self.y))
            elif self.stored_direction == False:
                screen.blit(stationaryL[self.stepIndex//14], (self.x, self.y))
            self.stepIndex += 1

    def hit_reg(self): #I have this set up such that attacking gives calculated data to victim, and being attacked takes data calculated from attacker
        # Hurt
        if self.hit:
            if self.hitpoints > 1:
                damage_fx.play()
            self.invincibility_timer = 1
            self.hitpoints -= 1
            if self.hit_direction == 0:
                self.dx += 25 #Distance of knockback
            if self.hit_direction == 1:
                self.dx -= 25
            self.hit = False
        self.invincibility_timer = timer(self.invincibility_timer, 20)
        if self.hitpoints <= 0:
            death_fx.play()
            self.game_over = True
        global game_over
        game_over = player.game_over
        # Attack
        for dummy in dummies:
            for bullet in self.bullets:
                if bullet.hitbox.colliderect(dummy.hitbox.x, dummy.hitbox.y, dummy.hitbox.width, dummy.hitbox.height):
                    if bullet.dx > 0:
                        dummy.hit_direction = 0
                    else:
                        dummy.hit_direction = 1
                    self.bullets.remove(bullet)
                    dummy.hit = True

    def shoot(self):
        self.hit_reg()
        # Append Bullets
        if (pygame.mouse.get_pressed()[0] and self.attack_timer == 0 and self.invincibility_timer == 0):
            shoot_fx.play()
            mouse_x, mouse_y = pygame.mouse.get_pos()
            bullet = Bullet(self.x, self.y, mouse_x - 20, mouse_y - 10) #These constants move the position of the bullet around where the mouse is
            self.bullets.append(bullet)
            self.attack_timer = 1
        self.attack_timer = timer(self.attack_timer, 35)
        # Apply Bullet Class Control to Bullets
        for bullet in self.bullets:
            bullet.move()
            if bullet.bounce_count > 1: #Constant is how many times bullet can bounce
                player.bullets.remove(bullet)

    def reset(self, x, y):
        # Walk
        self.x = x
        self.y = y
        self.dx = 0
        self.stored_direction = True #True = was facing right, False = was facing left
        self.face_right = False
        self.face_left = False
        self.stepIndex = 0
        # Jump
        self.vel_y = 0
        self.dy = 0
        self.jumped = False
        # Bullet
        self.bullets = []
        self.attack_timer = 0
        # Health
        self.hitbox = pygame.Rect(self.x, self.y, 64, 64)
        self.hit = False #If hit true
        self.hitpoints = 3 #Amount of health
        self.hit_direction = 0 #Keeps track of side hit for knockback purpose, 0 = hit from left, 1 = hit from right
        self.invincibility_timer = 0 #Sent to attacker to check if player can be hit
        self.game_over = False

class Bullet:
    def __init__(self, x, y, targetx, targety):
        self.x = x + 67 #These constants move the position of the bullet around where the player is
        self.y = y + 50
        self.targetx = targetx
        self.targety = targety
        # Bounce
        self.bounced_x = 1
        self.bounced_y = 1
        self.bounce_count = 0
        self.bounce_timer = 0
        # Aiming
        self.angle = math.atan2(self.targety - self.y, self.targetx - self.x) #Get angle to target in radians
        self.dy = math.sin(self.angle)*16 #Constant is bullet speed
        self.dx = math.cos(self.angle)*16
        # Hitbox
        self.hitbox = pygame.Rect(self.x, self.y, 0, 0)
 
    def move(self):
        self.x += self.dx * self.bounced_x
        self.y += self.dy * self.bounced_y
        self.bounce()
    
    def bounce(self):
        # Count Bounces and Track New Sprite Angle After Bounce
        for tile in world.tile_list: 
            # y Direction
            if tile[1].colliderect(self.hitbox.x, self.hitbox.y + self.dy, self.hitbox.width, self.hitbox.height) and self.bounce_timer == 0:
                self.bounce_timer = 1
                if self.dy > 0: # Moves bullet around the spot it bounced
                    self.y -= 10
                elif self.dy < 0:
                    self.y += 10
                self.bounced_y *= -1
                self.angle = 0 - self.angle
                self.bounce_count += 1
            # x Direction 
            elif tile[1].colliderect(self.hitbox.x + self.dx, self.hitbox.y, self.hitbox.width, self.hitbox.height) and self.bounce_timer == 0:
                self.bounce_timer = 1
                if self.dx > 0:
                    self.x -= 10
                elif self.dx < 0:
                    self.x += 10
                self.bounced_x *= -1
                self.angle = math.pi - self.angle
                self.bounce_count += 1
        self.bounce_timer = timer(self.bounce_timer, 2.5)

    def draw(self):
        bullet_img_rotated = pygame.transform.rotate(bullet_img, -(self.angle*180)/math.pi)
        # Hitbox
        self.hitbox = pygame.Rect(self.x, self.y, bullet_img_rotated.get_rect()[2] - 5, bullet_img_rotated.get_rect()[3] - 5)
        if SHOW_HITBOX:
            pygame.draw.rect(screen, (255,0,0), self.hitbox, 1)
        # Bullet
        screen.blit(bullet_img_rotated, (self.x, self.y))

class Dummy():
    def __init__(self, x, y):
        # Walk
        self.x = x
        self.y = y
        self.vel_x = 5 #Dummy walk speed
        self.stored_direction = False #True = was facing right, False = was facing left
        self.face_right = True
        self.face_left = False
        self.stepIndex = 0
        # AI stuff
        self.prev_x = x #For tracker method
        self.dx = 0 
        self.walk_timer = 100
        self.ai_direction = 1 #1 is right -1 is left, what direction bot will walk
        # Health
        self.hitbox = pygame.Rect(self.x, self.y, 64, 64)
        self.hit = False #If hit true
        self.hitpoints = 3 #Amount of health
        self.hit_direction = 0 #Keeps track of which side dummy was hit for knockback purpose, 0 = hit from left, 1 = hit from right
        
    def draw(self, screen):
        # Hitbox
        self.hitbox = pygame.Rect(self.x + 60, self.y + 30, 40, 75) # Constants: xpos and ypos of hitbox, width and height of hitbox
        if SHOW_HITBOX:
            pygame.draw.rect(screen, (0,0,0), self.hitbox, 1)
        # Sprite Animation
        self.tracker()
        if self.stepIndex >= 60: #This step index is a multiple of the amount of frames in the sequence to slow the frames
            self.stepIndex = 0
        if self.face_left:
            screen.blit(left[self.stepIndex//10], (self.x, self.y))
            self.stored_direction = False
            self.stepIndex += 1
        if self.face_right:
            screen.blit(right[self.stepIndex//10], (self.x, self.y))
            self.stored_direction = True
            self.stepIndex += 1
        if not self.face_left and not self.face_right:
            if self.stepIndex >= 56:
                self.stepIndex = 0
            if self.stored_direction == True:
                screen.blit(stationaryR[self.stepIndex//14], (self.x, self.y))
            elif self.stored_direction == False:
                screen.blit(stationaryL[self.stepIndex//14], (self.x, self.y))
            self.stepIndex += 1

    def tracker(self):
        # Know Direction Bot Is Moving For Animations
        self.dx = self.x - self.prev_x
        self.prev_x = self.x
        if self.dx > 0:
            self.face_right = True
            self.face_left = False
        elif self.dx < 0:
            self.face_left = True
            self.face_right = False
        else:
            self.face_right = False
            self.face_left = False

    def hit_reg(self):
        # Attack
        if self.hitbox.colliderect(player.hitbox.x, player.hitbox.y + player.dy, player.hitbox.width, player.hitbox.height):
            if self.dx > 0:
                player.hit_direction = 0
            else:
                player.hit_direction = 1
            if player.invincibility_timer == 0:
                player.hit = True
        # Hurt
        if self.hit:
            if self.hitpoints > 1:
                damage_fx.play()
            self.hitpoints -= 1
            if self.hit_direction == 0:
                self.x += 100 #Distance of knockback
            if self.hit_direction == 1:
                self.x -= 100
            self.hit = False      

    def move(self):
        self.hit_reg()
        self.x += self.vel_x * self.ai_direction
        self.walk_timer -= 1
        if self.walk_timer <= 0:
            self.ai_direction *= -1
            self.walk_timer = 100 #Same as in init


# Instances
world = World(WORLD_DATA) 
#Buttons
restart_button = Button(SCREEN_WIDTH//2 - 55, SCREEN_HEIGHT//2, restart_img)
start_button = Button(SCREEN_WIDTH//2 - 55, SCREEN_HEIGHT//2 - 60, start_img)
exit_button = Button(SCREEN_WIDTH//2 - 55, SCREEN_HEIGHT//2 + 60, exit_img)
#Player
player = Player(600, 600)
def player_attributes():
    player.move(userInput)
    player.shoot()
#Dummy
dummies = []
def dummy_attributes():
    if len(dummies) == 0: 
        dummy1 = Dummy(random.randint(200,1600), 600)
        dummies.append(dummy1)
    for dummy in dummies:
        dummy.move()
        if dummy.hitpoints <= 0:
            death_fx.play()
            dummies.remove(dummy)

# Draw Game
def draw_game():
    screen.blit(background_img, (0, 0))
    # Draw instances
    world.draw()
    player.draw(screen)
    for dummy in dummies:
        dummy.draw(screen)
    for bullet in player.bullets:
        bullet.draw()
    # Frame Settings and Show Fps
    clock.tick(FRAME_RATE)
    if SHOW_FPS:
        fps = str(int(clock.get_fps()))
        draw_text(fps, font_fps, (255,191,0), 10, 0)
    # Health Counter
    draw_text("Health: " + str(player.hitpoints), font_health, (255,255,255), 50, 950)
    # Restart button
    if game_over == True:
        restart_button.draw()


# Mainloop
run = True
while run:

    # Quit Game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # Main Menu
    if main_menu == True:
        screen.blit(menu_img, (0, 0))
        screen.blit(title_img, (SCREEN_WIDTH//2 - 270, SCREEN_HEIGHT//2 - 520))
        start_button.draw()
        exit_button.draw()
        if start_button.clicked == True:
            main_menu = False
        if exit_button.clicked == True:
            run = False
    else:
        # Frame consistency with movement
        curr_time = time.time()
        dt = curr_time - prev_time #Multiply or add this to variables affiliated with frames
        prev_time = curr_time

        # Input Update
        userInput = pygame.key.get_pressed()

        # Call Methods, Restart Game
        if restart_button.clicked == True:
            restart_button.clicked = False
            game_over = False
            player.reset(600, 600)
        if game_over == False: #Only if alive
            player_attributes()
            dummy_attributes()
    
    # Draw Game on Screen
        draw_game()
    pygame.display.update()
