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
# Type of arrow moving
FORCE_APPLY_TO_THE_DIRECTION = 1    # The arrows will have a force apply to it current direction which will cause the arrow to "drift"
VELOCITY_APPLY_TO_THE_DIRECTION = 2 # The arrows will have a velocity apply to it current direction which will cause the arrow to go straight ahead

# Constantes
FPS = 30
STEP_BY_FRAM = 10
CURSOR_REPULS_RADIUS = 50
NUM_ARROWS_X = 10
NUM_ARROWS_Y = 10
TYPE_GENERATION = RANDOM    # GENERATIV or RANDOM
NUM_OF_AROWS = 50           # (only for RANDOM)
ARROW_SIZE = (50, 200)      # Between the first and the second (only for RANDOM)
ARROW_ELASTICITY = 0.5
ARROW_MOVING_TYPE = FORCE_APPLY_TO_THE_DIRECTION    # FORCE_APPLY_TO_THE_DIRECTION or VELOCITY_APPLY_TO_THE_DIRECTION
ARROW_ROTATING_SPEED = 5
ARROW_ACCELERATION = 10
ARROW_MAX_SPEED = 1000
ARROW_DISTANCE_SCALING = 0.001
MIN_DISTANCE_SCALING = 0.5
MAX_DISTANCE_SCALING = 3.0
ARROW_MASS_MULTIPLIER = 10  # 0 produce an error

MOUSE_HIT_BOX_VISIBLE = False
ARROW_HIT_BOX_VISIBLE = False


def limit_velocity(body: pymunk.Body, gravity: tuple[float, float], damping: float, dt: float) -> None:
    """symply a function to limit the arrow's speed"""
    max_velocity = ARROW_MAX_SPEED
    pymunk.Body.update_velocity(body, gravity, damping, dt)
    l = body.velocity.length
    if l > max_velocity:
        scale = max_velocity / l
        body.velocity = body.velocity * scale

class Arrow(pygame.sprite.Sprite):
    """a class to have arrows trying to reach a certain point"""

    def __init__(self, x: float, y: float, x_size: float, y_size: float, color: tuple[int, int, int]) -> None:
        """initialize the arrow"""
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
        self.shape.elasticity = ARROW_ELASTICITY
        space.add(self.body, self.shape)

    @property
    def rect(self) -> pygame.Rect:
        """get the rect of the arrow

        Returns:
            pygame.Rect: the rect of the arrow
        """
        rect = self.image.get_rect(center=self.surface.get_rect().center)
        rect.center = self.x, self.y
        return rect

    def get_angle(self, x: float, y: float) -> float:
        """get the angle between the arrow and the given point

        Args:
            x (float): the x pos of the point
            y (float): the y pos of the point

        Returns:
            float: the angle in degrees
        """
        angle_radions = math.atan2(y - self.y, x - self.x)
        angle_degrees = math.degrees(angle_radions)
        return angle_degrees

    def get_vector(self, angle: float, x: float, y: float) -> tuple[float, float]:
        """get the vector of the given angle scaled on the distance between the arrow and the given point

        Args:
            angle (float): the angle in degrees
            x (float): the x pos of the point
            y (float): the y pos of the point

        Returns:
            tuple[float, float]: the vecteur
        """
        angle_radians = math.radians(angle)
        distance = self.get_distance(x, y)
        distance_scaling =  min(MAX_DISTANCE_SCALING, max(MIN_DISTANCE_SCALING, distance * ARROW_DISTANCE_SCALING))
        if ARROW_MOVING_TYPE == FORCE_APPLY_TO_THE_DIRECTION:
            multiplier = FPS * STEP_BY_FRAM * ARROW_ACCELERATION * self.mass * distance_scaling
        elif ARROW_MOVING_TYPE == VELOCITY_APPLY_TO_THE_DIRECTION:
            multiplier = FPS * ARROW_ACCELERATION * distance_scaling
        x = math.cos(angle_radians) * multiplier
        y = -math.sin(angle_radians) * multiplier
        return x, y

    def get_distance(self, x: float, y: float) -> float:
        """get the distance between the arrow and the given point

        Args:
            x (float): the x pos of the point
            y (float): the y pos of the point

        Returns:
            float: the distanc
        """
        return ((x-self.x)**2 + (y-self.y)**2)**0.5

    def apply_force(self, force: tuple[float, float]) -> None:
        """apply a force to the arrow

        Args:
            force (tuple[float, float]): the force to apply
        """
        x1, y1 = self.body.velocity
        x2, y2 = force
        x = x2 - x1
        y = y2 - y1
        if ARROW_MOVING_TYPE == VELOCITY_APPLY_TO_THE_DIRECTION:
            self.body.velocity += x, y
        elif ARROW_MOVING_TYPE == FORCE_APPLY_TO_THE_DIRECTION:
            self.body.force = x, y

    def apply_angle(self, angle: float) -> None:
        """apply an angle force to reach the given angle

        Args:
            angle (float): the angle to reach in degrees
        """
        body_angle = math.degrees(self.body.angle) % 360
        angle_diffrence = angle - body_angle
        if angle_diffrence > 180:
            angle_diffrence -= 360
        if angle_diffrence < -180:
            angle_diffrence += 360
        self.body.angular_velocity = math.radians(angle_diffrence*ARROW_ROTATING_SPEED)

    def update(self, pos: tuple[float, float]) -> None:
        """update the arrow

        Args:
            pos (tuple[float, float]): the position to reach
        """
        self.x, self.y = self.body.position
        angle = self.get_angle(*pos)
        body_angle = math.degrees(self.body.angle)
        vecteur = self.get_vector(-body_angle, *pos)
        self.apply_angle(angle)
        self.apply_force(vecteur)
        self.image = pygame.transform.rotate(self.surface, -body_angle)
        if ARROW_HIT_BOX_VISIBLE:
            self.draw()

    def draw(self) -> None:
        """draw the hitbox of the arrow"""
        points = [v.rotated(self.body.angle) + self.body.position for v in self.shape.get_vertices()]
        pygame.draw.polygon(screen, "#FFFFFF", points)

class Cursor:
    """a classe for the cursor to have collision"""

    def __init__(self) -> None:
        """initialize the cursor"""
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = pygame.mouse.get_rel()
        self.shape = pymunk.shapes.Circle(self.body, CURSOR_REPULS_RADIUS)
        self.shape.elasticity = 1

    def update(self) -> None:
        """update the cursor"""
        dep = pygame.mouse.get_rel()
        dep = [i * FPS for i in dep]
        self.body.velocity = dep
        if MOUSE_HIT_BOX_VISIBLE:
            self.draw()

    def draw(self) -> None:
        """draw the hitbox of the cursor"""
        pygame.draw.circle(screen, "#FFFFFF", self.body.position, CURSOR_REPULS_RADIUS)

    def disable(self) -> None:
        """disaple the cursor's collisions"""
        space.remove(self.body, self.shape)

    def enable(self) -> None:
        """enable the cursor's collisions"""
        self.body.position = pygame.mouse.get_pos()
        space.add(self.body, self.shape)

# Generate the arrows
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

# Creat the cursor object
cursor = Cursor()
cursor.enable()

while True:
    # Events gestion
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    # Update and draw the object
    screen.fill("#000000")
    cursor.update()
    arrow_group.update(pos=pygame.mouse.get_pos())
    arrow_group.draw(screen)

    # Update the physic simulation
    dt = dec(1) / FPS
    for i in range(STEP_BY_FRAM):
        space.step(dt / STEP_BY_FRAM)

    pygame.display.update()
    clock.tick(FPS)


