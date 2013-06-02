# -*- coding: utf-8 -*-
import pygame
import socket
import time
from multiprocessing import Process, Queue


def recv(q, r):
    host = ''
    port = 50000
    backlog = 5
    size = 1024 

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host,port))
    s.listen(backlog) 
    while r.empty():
        client, address = s.accept()
        data = client.recv(size)
        q.put(data)
        client.close()



class Team(object):
    def __init__(self, name, points=0):
        self.name = name
        self.points = points


class Round(object):
    def __init__(self, r):
        l = r.split('\n')
        a = [line.split(";") for line in l[2:]]
        a = [(q, int(p)) for (q,p) in a]
        self.question = r[1].strip()
        self.answers = a
        self.num = int(r[0])
        self.mult = 1 if self.num == 1 else self.num - 1
        self.num_answers = min(len(self.answers), 7 - self.num)
        self.wrongs = 0
        self.points = 0
        self.solved = []

class Game(object):
    def __init__(self):
        self.team_a = None
        self.team_b = None
        self._rounds = {}
        self._cur_round = None
        self.rtype = None

    def add_round(self, r):
        self._rounds[r.num] = r

    def set_round(self, n):
        self._cur_round = self._rounds[n]

    def set_team_a(self, name, points=0):
        self.team_a = Team(name, points) 

    def set_team_b(self, name, points=0):
        self.team_b = Team(name, points) 

    def check(self):
        if self._rounds.keys() != list(range(1,5)):
            return False
    
    def get_wrongs(self):
        if self._cur_round:
            return self._cur_round.wrongs
        else:
            return 3

    def get_mult(self):
        if self._cur_round:
            return self._cur_round.mult
        else:
            return 0

    def get_round(self):
        return self._cur_round

    def load(self, filename):
        l = open(filename).read()
        rnds,f = l.split("#final")
        rnds = rnds.strip().split("#round")
        for rnd in rnds[1:]:
            r = Round(rnd.strip())
            self.add_round(r)
                
    def solve(self, num):
        self._cur_round.solved.append(num)



class Renderer(object):
    def __init__(self):
        self._black = ( 0, 0, 0)
        self._white = ( 255, 255, 255)
        self._green = ( 0, 255, 0)
        self._red = ( 255, 0, 0)
        pygame.init()
        pygame.mixer.init()
        self._width = 800
        self._height = 600
        #self._screen=pygame.display.set_mode([self._width,self._height], pygame.FULLSCREEN | pygame.HWSURFACE)
        self._screen=pygame.display.set_mode([self._width,self._height], pygame.HWSURFACE)
        pygame.display.set_caption("sd")
        self._done=False
        self._clock=pygame.time.Clock()
        self._big_font_size = self._height // 12
        self._small_font_size = self._height // 14
        self._big_font = pygame.font.SysFont("DejaVu Sans Mono", self._big_font_size)
        self._small_font = pygame.font.SysFont("DejaVu Sans Mono", self._small_font_size)
        self._frame_count = 0
        self._frame_rate = 60
        self._title = "Studierenden Duell 2013"
        self._solving = False
        self._solving_num = None
        self._solving_state = 0
        self._solving_start = 0
        self._solved = []
        self._alen = 20
        self._sound_answer = pygame.mixer.Sound("answer.wav")
        self._sound_points = pygame.mixer.Sound("points.wav")

    def render(self, game=None):
        for event in pygame.event.get(): # User did something
            if event.type == pygame.QUIT: # If user clicked close
                self._done=True # Flag that we are done so we exit this loop
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    self._done = True
        self._screen.fill(self._black)

        text = self._big_font.render(self._title,True,self._green)
        self._screen.blit(text, [self.center(text) ,0])
        self.draw_content(game)
        self._clock.tick(self._frame_rate)
        self._frame_count += 1
        pygame.display.flip()
        return self._done

    def draw_content(self, game=None):
        if not game:
            self.draw_idle()
        elif game.rtype == "round":
            self.draw_round(game)
        else:
            self.draw_final(game)

    def draw_round(self, game):
        rnd = game.get_round()
        for i in range(rnd.num_answers):
            a, p = rnd.answers[i]
            if i in game.get_round().solved and not i in self._solved:
                self._solving = True
                self._solving_num = i
                self._solving_state = 1
                self._solving_start = self._frame_count
                self._solved.append(i)
                self._sound_answer.play()
            if self._solving and self._solving_num == i:
                a,p = self.solve_answer(i, game)
            elif not i in self._solved:
                a = "."*self._alen
                p = "--"
            self.draw_answer(i, a, p) 
        self.draw_points(game)

    def draw_points(self, game):
        last_y = self._height - self._big_font.get_linesize()
        snd_last_y = last_y - self._big_font.get_linesize()
        # team a
        output_string = '{}'.format(game.team_a.name)
        text = self._big_font.render(output_string.encode("utf-8"),True,self._green)
        self._screen.blit(text, [0, snd_last_y])
        output_string = '{}'.format(game.team_a.points)
        text = self._big_font.render(output_string,True,self._green)
        self._screen.blit(text, [0, last_y])

        #team_b
        output_string = '{}'.format(game.team_b.name)
        text = self._big_font.render(output_string.encode("utf-8"),True,self._green)
        self._screen.blit(text, [self._width - text.get_size()[0], snd_last_y])
        output_string = '{}'.format(game.team_b.points)
        text = self._big_font.render(output_string,True,self._green)
        self._screen.blit(text, [self._width - text.get_size()[0], last_y])

        #wrong and multi
        output_string = '{} {:<3}'.format(game.get_round().points, "X"*game.get_wrongs())
        text = self._big_font.render(output_string,True,self._green)
        self._screen.blit(text, [self.center(text), snd_last_y])
        output_string = '{}x'.format(game.get_mult())
        text = self._big_font.render(output_string,True,self._green)
        self._screen.blit(text, [self.center(text), last_y])

    def draw_final(self, game):
        pass
        
    def solve_answer(self, num, game):
        a,p = game.get_round().answers[self._solving_num]
        if self._solving_state == self._alen:
            self._sound_points.play()
            self._solving = False
        else:
            p = "--"
        n = min(self._solving_state, len(a))
        m = self._solving_state - n
        s = "{}{}{}".format(a[:n], " "*m, "."*(self._alen - (n+m)))
        self._solving_state += ((self._frame_count - self._solving_start) % 10) // 9
        return s,p


    def draw_idle(self):
        y = ((self._height) / 2) * 0.9
        display_text = "Gleich geht's weiter"
        text = self._big_font.render(display_text, True, self._green)
        self._screen.blit(text, [self.center(text),y])


    def draw_answer(self, num, atext="."*16, points="--"):
        y = ((self._height * 0.7) / 5) * 0.9 * (num + 1)
        display_text = '{}: {:<20} {:>2}'.format((num + 1), atext.encode("utf-8"), points)
        text = self._small_font.render(display_text, True, self._green)
        self._screen.blit(text, [self.center(text),y])

    def center(self, text):
        return (self._width - text.get_size()[0]) // 2



class Session(object):
    def __init__(self, q):
        self.game = None
        self._q = q

    def do(self,cmd):
        c = cmd.split("#")
        if c[0] == "load":
            self.game = Game()
            self.game.set_team_a("foo")
            self.game.set_team_b("bar", 23)
            self.game.load(c[1])
        elif c[0] == "setround":
            self.game.set_round(int(c[1]))
            self.game.rtype = "round"
        elif c[0] == "solve":
            self.game.solve(int(c[1]))

    def run(self):
        running = False
        while self._q.empty():
            time.sleep(0.1)
        if self._q.get() == "init":
            running = True
        
        
        r = Renderer()
        while not r.render(self.game) and running:
            if not self._q.empty():
                self.do(self._q.get())
        
        pygame.quit ()


def main():
    q = Queue()
    r = Queue()

    recvr = Process(target=recv, args=(q,r))
    recvr.start()
    s = Session(q)
    s.run()
    r.put("stopit")
    recvr.join()

if __name__ == '__main__':
    main()
