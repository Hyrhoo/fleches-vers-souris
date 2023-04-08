import pygame, pymunk, math, random, sys
from decimal import Decimal as dec

pygame.init()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 900
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

space = pymunk.space.Space()
space.gravity = (0, 0)

# Type of generation
GENERATIV = 1
RANDOM = 2

NUM_ARROWS_X = 10
NUM_ARROWS_Y = 10
TYPE_GENERATION = RANDOM   # GENERATIV or RANDOM
NUM_OF_AROWS = 20          # for RANDOM
FPS = 30
STEP_BY_FRAM = 10
REPULS_RADIUS = 100
ARROW_ROTATING_SPEED = 10
ARROW_ACCELERATION = 10
ARROW_MAX_SPEED = 1000
ARROW_ELASTICITY = 0.5
ARROW_SIZE = (50, 200)   # between the first and the second
ARROW_MASS_MULTIPLIER = 10  # 0 produce an error

MOUSE_HIT_BOX_VISIBLE = False
ARROW_HIT_BOX_VISIBLE = False


def limit_velocity(body: pymunk.Body, gravity, damping, dt):
    max_velocity = ARROW_MAX_SPEED
    pymunk.Body.update_velocity(body, gravity, damping, dt)
    l = body.velocity.length
    if l > max_velocity:
        scale = max_velocity / l
        body.velocity = body.velocity * scale

class Arrow(pygame.sprite.Sprite):

    def __init__(self, x, y, x_size, y_size, color) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.size = (x_size, y_size)
        self.points = [(0, self.size[1]*0.25), (self.size[0]*0.75, self.size[1]*0.25), (self.size[0]*0.75, 0), (self.size[0], self.size[1]*0.50),
                       (self.size[0]*0.75, self.size[1]), (self.size[0]*0.75, self.size[1]*0.75), (0, self.size[1]*0.75)]
        self.surface = pygame.Surface(self.size).convert_alpha()
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.polygon(self.surface, color, self.points)
        self.image = self.surface.copy()
        self.mass = x_size * y_size * ARROW_MASS_MULTIPLIER
        moment = pymunk.moment_for_poly(self.mass, self.points)
        self.body = pymunk.Body(self.mass, moment)
        self.body.position = self.x, self.y
        self.body.velocity_func = limit_velocity
        self.shape = pymunk.Poly(self.body, [(x-self.size[0]/2, y-self.size[1]/2) for x, y in self.points])
        self.shape.friction = 0.0
        self.shape.elasticity = ARROW_ELASTICITY
        space.add(self.body, self.shape)

    @property
    def rect(self):
        rect = self.image.get_rect(center=self.surface.get_rect().center)
        rect.center = self.x, self.y
        return rect
    
    def get_angle(self, x, y):
        angle_radions = math.atan2(y - self.y, x - self.x)
        angle_degrees = math.degrees(angle_radions)
        return angle_degrees
    
    def get_vecteur(self, angle, x, y):
        x = math.cos(math.radians(angle)) * FPS * STEP_BY_FRAM * ARROW_ACCELERATION * self.mass
        y = -math.sin(math.radians(angle)) * FPS * STEP_BY_FRAM * ARROW_ACCELERATION * self.mass
        return x, y

    def get_distance(self, x, y):
        return ((x-self.x)**2 + (y-self.y)**2)**0.5
    
    def apply_force(self, force):
        x1, y1 = self.body.velocity
        x2, y2 = force
        x = x2 - x1
        y = y2 - y1
        self.body.force = x, y
    
    def apply_angle(self, angle):
        body_angle = math.degrees(self.body.angle) % 360
        angle_diffrence = angle - body_angle
        if angle_diffrence > 180:
            angle_diffrence -= 360
        if angle_diffrence < -180:
            angle_diffrence += 360
        self.body.angular_velocity = math.radians(angle_diffrence*ARROW_ROTATING_SPEED)

    def update(self, pos) -> None:
        self.x, self.y = self.body.position
        angle = self.get_angle(*pos)
        body_angle = math.degrees(self.body.angle)
        vecteur = self.get_vecteur(-body_angle, *pos)
        self.apply_angle(angle)
        self.apply_force(vecteur)
        self.image = pygame.transform.rotate(self.surface, -body_angle)
        if ARROW_HIT_BOX_VISIBLE:
            self.draw()
    
    def draw(self):
        points = [v.rotated(self.body.angle) + self.body.position for v in self.shape.get_vertices()]
        pygame.draw.polygon(screen, "#FFFFFF", points)

class Cursor:

    def __init__(self) -> None:
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pygame.mouse.get_rel()
        self.shape = pymunk.shapes.Circle(self.body, REPULS_RADIUS)
        self.shape.elasticity = 1
    
    def update(self):
        dep = pygame.mouse.get_rel()
        dep = [i * FPS for i in dep]
        self.body.velocity = dep
        if MOUSE_HIT_BOX_VISIBLE:
            self.draw()
    
    def draw(self):
        pygame.draw.circle(screen, "#FFFFFF", self.body.position, REPULS_RADIUS)

    def disable(self):
        space.remove(self.body, self.shape)
    
    def enable(self):
        space.add(self.body, self.shape)

# generate the arrows
arrow_group = pygame.sprite.Group()
if TYPE_GENERATION == RANDOM:
    for i in range(NUM_OF_AROWS):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        lenght = random.randint(*ARROW_SIZE)
        height = lenght / 2
        arrow = Arrow(x, y, lenght, height, color)
        arrow_group.add(arrow)

elif TYPE_GENERATION == GENERATIV:
    x_space = (SCREEN_WIDTH/NUM_ARROWS_X)
    y_space = (SCREEN_HEIGHT/NUM_ARROWS_Y)
    for x in range(NUM_ARROWS_X):
        x = x*x_space + x_space/2
        for y in range(NUM_ARROWS_Y):
            y = y*y_space + y_space/2
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            arrow = Arrow(x, y, 100, 50, color)
            arrow_group.add(arrow)

# creat the cursor object
cursor = Cursor()
cursor.enable()

while True:
    # events gestion
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    # update and draw the object
    screen.fill("#000000")
    cursor.update()
    arrow_group.update(pos=pygame.mouse.get_pos())
    arrow_group.draw(screen)

    # update the physic simulation
    dt = dec(1) / FPS
    for i in range(STEP_BY_FRAM):
        space.step(dt / STEP_BY_FRAM)

    pygame.display.update()
    clock.tick(FPS)


