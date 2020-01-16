import pygame
import neat
import os, time, random
import pickle
pygame.font.init()

GEN = 0

WIN_WIDTH = 600
WIN_HEIGHT = 800

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BG_IMG = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")),(WIN_WIDTH, WIN_HEIGHT))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))

SCORE_FONT = pygame.font.SysFont("comicsans",50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25 #rotation degree
    ROT_VEL = 15 #rotation velocity, how many times we're gonna rotate the bird in teach frame
    ANIMATION_TIME = 5 #how long to show each bird animation, the process of flapping the wings

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0 # how tilted the image is
        self.tick_count = 0 #keeps track of when we last jump/ how many ticks we've been moving forward
        self.vel = 0
        self.heigth = self.y #will be used to know were the bird was before jumping
        self.img_count = 0 # to know what image we're using right now
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5 # because (0,0) is the coordinate of the top left, if we want to go up we need a negative velocity and down a positive one
        self.tick_count = 0
        self.heigth = self.y

    def move(self):
        self.tick_count +=1 # a frame/tick went by

        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2 #displacement, how much to move
        #at the beginning of the jump: -10.5*1+1.5 = -9, as time advances it "increases"
        # and the displacement begins to turn positive, making the bird go lower

        if displacement>=10: # terminal velocity, the bird can't go down faster
            displacement = 10
        if displacement<0:
            displacement-=2 #fine tunes the movement a bit

        self.y = self.y + displacement
        # if we're going up or if we're kinda above the place we started
        if displacement<0 or self.y < self.heigth:
            #one if maybe missig
                self.tilt = self.MAX_ROTATION #when we go up we just want to rotate slightly
        else:
            if self.tilt >-90:
                self.tilt -= self.ROT_VEL #when we go down we want to ratate the full 90º, to look like a nose dive


    def draw(self, win): #the window
        self.img_count += 1 # fow how many frames we've shown an image

        #draws the wings flapping
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0 # completes the loop, bird returns to normal state

        # just for image stabilization
        if self.tilt <= -80:
            self.img = self.IMGS[1] # if we're going down too hard, just stabilize the wings
            self.img_count = self.ANIMATION_TIME *2 # this way when we jump the correct image(3) shows up
            # because we're already in the second image

        rotated_image = pygame.transform.rotate(self.img, self.tilt) #rotates the image but doesn't center it
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center) #rect = rectangle

        win.blit(rotated_image, new_rect.topleft) #topleft is the position, blit just draws

    #return a object mask to know when collisions happend
    def get_mask(self):
        return  pygame.mask.from_surface(self.img)
    #a mask is just a matrix indicating where the image's pixels are

class Pipe:
    GAP = 180 # space betwen bottom and top pipe
    VEL= 4 #since the bird isn't moving in the x plane, but the environment is

    def __init__(self,x): #we don't have an y, because it will be random
        self.x = x
        self.height = 0 #coordinate of the tip of top pipe

        self.top = 0 # where the top pipe is drawn, the entrance coordinate
        self.bottom =0 # where the bottom pipe is drawn
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False #if the bird has already passed the pipe, helpful for collision purposes
        self.set_height()

    def set_height(self):
        #for the top pipe
        self.height = random.randrange(50,350) # remember- 50 at the top, 450 almost at the bottom
        self.top = self.height-self.PIPE_TOP.get_height() #top left coordinate for it to be drawn, ex : 300-1500 = -1200, height were the pipe begins to be drawn
        #for the bottom pipe
        #since the top left coordinate of bottom pipe already is were we want it to be drawn, we just need to add the gap
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL #just move the pipe a bit to the left for each tick

    def draw(self,win):
        win.blit(self.PIPE_TOP,(self.x,self.top))
        win.blit(self.PIPE_BOTTOM,(self.x,self.bottom))

    def collide(self,bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #offset- distance between the bird mask and the pipe mask
        top_offset = (self.x-bird.x, self.top - round(bird.y)) # we can't have decimal numbers
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) # the point of overlap between the masks, if they don't colide, returns None
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or  t_point:
            return True

        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    def __init__(self,y):
        self.y = y
        #we have 2 images, one in front of the other
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):

        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #when the first image exists the screen, it moves to the front of the second image
        if self.x1 + self.WIDTH < 0:
            self.x1= self.x2+self.WIDTH

        # when the second image exists the screen, it moves to the front of the already moved first image
        if self.x2 + self.WIDTH <0:
            self.x2 = self.x1 +self.WIDTH

    def draw(self, win):
        win.blit(self.IMG,(self.x1, self.y))
        win.blit(self.IMG,(self.x2, self.y))



def draw_window(win, birds ,pipes,base, score, generation):
    win.blit(BG_IMG, (0,0))
    for pipe in pipes:
        pipe.draw(win)

    text = SCORE_FONT.render("SCORE: "+str(score),1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(),10)) # so it always fits the screen when it increases




    base.draw(win)
    if isinstance(birds,list):
         text = SCORE_FONT.render("GEN: " + str(generation), 1, (255, 255, 255))
         win.blit(text, (WIN_WIDTH - 60 - text.get_width(), 50))  # so it always fits the screen when it increases

         for bird in birds:
            bird.draw(win)
    else:
        birds.draw(win)
    pygame.display.update()


def eval_genomes(genomes, config):
    birds = []
    nets = []
    ge = [] #list of genomes, used to change genomes
    base = Base(650)
    pipes = [Pipe(700)]

    global GEN
    GEN+=1
    for genome_id,genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(300,300))
        genome.fitness = 0
        ge.append(genome)




    win = pygame.display.set_mode((WIN_WIDTH,WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True
    while run:
        clock.tick(30) # 30fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()

            '''if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()'''

        pipe_ind = 0
        if len(birds) > 0: # if there are still birds alive
            if len(pipes) > 1 and  birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width(): #we use bird[0} because all birds have the same x
                pipe_ind = 1 # if we passed the first pipe, look at the second, since everytime we pass a pipe it will be removed and a new one will be created afterwards, this works

        else: # if there are no birds
            run = False
            break
        for i, bird in enumerate(birds):
            bird.move()
            ge[i].fitness+=0.1 # encoraging for staying alive

            dist_top =  abs(bird.y - pipes[pipe_ind].height)
            dist_bot =  abs(bird.y - pipes[pipe_ind].bottom)
            output = nets[i].activate((bird.y, dist_top, dist_bot))

            if output[0] > 0.5: #output is a list of the outputs off all the neurons, because we only have one neuron, it's the first element in the list
                bird.jump()

        rem = [] #removed pipes
        add_pipe = False #initializing variable
        for pipe in pipes:
            for i,bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[i].fitness -=1
                    birds.pop(i)
                    nets.pop(i)
                    ge.pop(i)


                if not pipe.passed and pipe.x < bird.x:  # if the bird has passed the pipe
                    pipe.passed = True
                    add_pipe = True


            if pipe.x + pipe.PIPE_TOP.get_width()<0: # if it is no longer on the screen
                rem.append(pipe) #remove pipe

            pipe.move()

        if add_pipe:
            score+=1
            for g in ge:
                g.fitness+=5 #increasing the fitness of all the genomes who are still on the list
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        for i,bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 650 or bird.y < 0: # if it hits the base or the top(y<0)
                birds.pop(i)
                nets.pop(i)
                ge.pop(i)

        base.move()


        draw_window(win, birds, pipes, base,score,GEN)

        # break if score gets large enough
        if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            for node in nets[0].node_evals:
                print(node)
            break



def game_without_training(network):
    bird = Bird(300,300)
    base = Base(650)
    pipes = [Pipe(700)]

    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    score = 0
    run = True
    while run:
        clock.tick(30)  # 30fps
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()

        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # we use bird[0} because all birds have the same x
            pipe_ind = 1  # if we passed the first pipe, look at the second, since everytime we pass a pipe it will be removed and a new one will be created afterwards, this works

        bird.move()

        dist_top = abs(bird.y - pipes[pipe_ind].height)
        dist_bot = abs(bird.y - pipes[pipe_ind].bottom)
        output = network.activate((bird.y, dist_top, dist_bot))

        if output[0] > 0.5:  # output is a list of the outputs off all the neurons, because we only have one neuron, it's the first element in the list
            bird.jump()

        rem = []  # removed pipes
        add_pipe = False  # initializing variable
        for pipe in pipes:
            if pipe.collide(bird):
                pygame.quit()
            if not pipe.passed and pipe.x < bird.x:  # if the bird has passed the pipe
                pipe.passed = True
                add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:  # if it is no longer on the screen
                rem.append(pipe)  # remove pipe

            pipe.move()

        if add_pipe:
            score+=1
            pipes.append(Pipe(600))

        for r in rem:
            pipes.remove(r)

        base.move()

        draw_window(win, bird, pipes, base, score,None) # we are no longer interested in the generation



def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    p = neat.Population(config) #population

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    p.run(eval_genomes,50) #eval_genomes is the fitness function, max generations = 50


if __name__ ==  "__main__":
    try:
        best = pickle.load(open( "best.pickle", "rb" ))
        game_without_training(best)
    except FileNotFoundError:
        local_directory = os.path.dirname(__file__)
        config_path = os.path.join(local_directory, "config-feedforward.txt")
        run(config_path)

