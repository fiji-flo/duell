# -*- coding: utf-8 -*-
import pygame
import time
import BaseHTTPServer
import select
import urllib
import errno

from multiprocessing import Process, Queue


def srvr(q, r, x):
    site = open("html.html").read()
    jq = open("jquery-2.0.2.min.js").read()

    class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

        def do_HEAD(s):
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

        def do_GET(s):
            """Respond to a GET request."""
            print(s.headers)
            #r, msg = s.deal_get()
            #print(str(r)+": "+msg)
            
            s.send_response(200)
            if "jquery-2.0.2.min.js" in s.path:
                s.send_header("Content-type", "text/javascript")
                s.end_headers()
                s.wfile.write(bytes(jq))
                return
            elif "sddo" in s.path:
                s.send_header("Content-type", "text")
                s.end_headers()
                q.put(urllib.unquote(s.path.split("?")[1]))
                data = r.get(True,2 )
                s.wfile.write(bytes(data))
                return
            s.send_header("Content-type", "text/html")
            s.end_headers()
            s.gen_site()

        def finish(s):
            pass

        def gen_site(s):
            s.wfile.write(bytes(site))


    def _eintr_retry(func, *args):
        """restart a system call interrupted by EINTR"""
        while True:
            try:
                return func(*args)
            except (OSError, select.error) as e:
                if e.args[0] != errno.EINTR:
                    raise

    def run_server(httpd):
        running = True
        try:
            while running:
                if not x.empty():
                    running = False
                rl, w, e = _eintr_retry(select.select, [httpd], [], [], 0.5)
                if httpd in rl:
                    httpd._handle_request_noblock()
        finally:
            pass


        

    def start_server():
        server_class = BaseHTTPServer.HTTPServer
        httpd = server_class(("127.0.0.1", 8001), MyHandler)
        print(time.asctime(), "Server Starts - %s:%s" % ("127.0.0.1", 8001))
        try:
            run_server(httpd)
        except KeyboardInterrupt:
            httpd.server_close()
            print(time.asctime(), "Server Stops - %s:%s" % ("127.0.0.1", 8001))
            return    
        httpd.server_close()
        print(time.asctime(), "Server Stops - %s:%s" % ("127.0.0.1", 8001))


    start_server()

class Team(object):
    def __init__(self, name, points=0):
        self.name = name
        self.points = points

class Question(object):
    def __init__(self, r):
        l = r.split('\n')
        a = [line.split(";") for line in l[2:] if line != ""]
        a = [(qp[0], int(qp[1])) for qp in a if len(qp) == 2]
        self.question = l[1].strip()
        self.answers = a

class Round(Question):
    def __init__(self, r):
        super(Round, self).__init__(r)
        self.num = int(r[0])
        self.mult = 1 if self.num == 1 else self.num - 1
        self.num_answers = min(len(self.answers), 7 - self.num)
        self.wrongs = 0
        self.points = 0
        self.solved = []

    def get_data(self):
        ret = "{}###{}".format(self.question, "##".join(["{}#{}".format(a,p) for (a,p) in self.answers]))
        return ret

class Final(object):
    def __init__(self, f):
        self.questions = []
        self.points_a = 0
        self.points_b = 0
        self.hide = False
        self.solved_a = {}
        self.solved_b = {}
        fqs = f.strip().split("#fin")
        for fq in fqs[1:]:
            q = Question(fq.strip())
            self.questions.append(q)

    def get_data(self):
        qs = []
        for q in self.questions:
            qs.append("{}###{}".format(q.question, "##".join(["{}#{}".format(a,p) for (a,p) in q.answers])))
        return "####".join(qs)

class Game(object):
    def __init__(self):
        self.team_a = None
        self.team_b = None
        self._rounds = {}
        self._cur_round = None
        self.final = None
        self.rtype = None
        self.solving = False
        self.solving_a = False
        self.solving_b = False
        self.solving_num = None
        self.solving_state = 0
        self.solving_start = 0
        self.solved = []
        self.solved_fin_a = {}
        self.solved_fin_b = {}
        self.wrongs = 0

    def add_round(self, r):
        self._rounds[r.num-1] = r

    def set_round(self, n):
        self.rtype = "round"
        self.solving = False
        self.solving_num = None
        self.solving_state = 0
        self.solving_start = 0
        self.solved = []
        self.wrongs = 0
        self._cur_round = self._rounds[n]

    def set_final(self):
        self.rtype = "final"
        self.solving_a = False
        self.solving_b = False
        self.solving_num = None
        self.solving_state = 0
        self.solving_start = 0
        self.solved_fin_a = {}
        self.solved_fin_b = {}
        self.wrongs = 0

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

    def make_points(self, team):
        p = team.points
        for i in self.solved:
            p += (self._cur_round.answers[i][1]*self._cur_round.mult)
        team.points = p


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
        self.final = Final(f.strip())
                
    def solve(self, num):
        self._cur_round.solved.append(num)

    def wrong(self):
        self._cur_round.wrongs = min(self._cur_round.wrongs, 3)



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
        self._small_font_size = self._height // 16
        self._big_font = pygame.font.SysFont("DejaVu Sans Mono", self._big_font_size)
        self._small_font = pygame.font.SysFont("DejaVu Sans Mono", self._small_font_size)
        self._frame_count = 0
        self._frame_rate = 60
        self._title = "Studierenden Duell 2013"
        self._alen = 20
        self._sound_answer = pygame.mixer.Sound("answer.wav")
        self._sound_points = pygame.mixer.Sound("points.wav")
        self._sound_wrong = pygame.mixer.Sound("wrong.wav")

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
        elif game.rtype == "final":
            self.draw_final(game)
        else:
            self.draw_idle()

    def draw_round(self, game):
        rnd = game.get_round()
        for i in range(rnd.num_answers):
            a, p = rnd.answers[i]
            if i in game.get_round().solved and not i in game.solved:
                game.solving = True
                game.solving_num = i
                game.solving_state = 1
                game.solving_start = self._frame_count
                game.solved.append(i)
                self._sound_answer.play()
            if game.solving and game.solving_num == i:
                a,p = self.solve_answer(i, game, a, p)
            elif not i in game.solved:
                a = "."*self._alen
                p = "--"
            self.draw_answer(i, a, p) 
        self.draw_points(game)

    def draw_points(self, game):
        last_y = self._height - self._small_font.get_linesize()
        snd_last_y = last_y - self._small_font.get_linesize()
        # team a
        output_string = '{}'.format(game.team_a.name)
        text = self._small_font.render(output_string.encode("utf-8"),True,self._green)
        self._screen.blit(text, [0, snd_last_y])
        output_string = '{}'.format(game.team_a.points)
        text = self._small_font.render(output_string,True,self._green)
        self._screen.blit(text, [0, last_y])

        #team_b
        output_string = '{}'.format(game.team_b.name)
        text = self._small_font.render(output_string.encode("utf-8"),True,self._green)
        self._screen.blit(text, [self._width - text.get_size()[0], snd_last_y])
        output_string = '{}'.format(game.team_b.points)
        text = self._small_font.render(output_string,True,self._green)
        self._screen.blit(text, [self._width - text.get_size()[0], last_y])

        #wrong and multi
        if game.wrongs < game.get_wrongs():
            game.wrongs += 1
            self._sound_wrong.play()
        output_string = '{} {:<3}'.format(game.get_round().points, "X"*game.get_wrongs())
        text = self._small_font.render(output_string,True,self._green)
        self._screen.blit(text, [self.center(text), snd_last_y])
        output_string = '{}x'.format(game.get_mult())
        text = self._small_font.render(output_string,True,self._green)
        self._screen.blit(text, [self.center(text), last_y])

    def draw_final(self, game):
        for i in range(5):
            a,p = None, None
            if not i in game.solved_fin_a.keys() or game.final.hide:
                a = "."*self._alen
                p = "--"
            else:
                a,p = game.final.questions[i][game.solved_fin_a[i]]
            if i in game.final.solved_a.keys() and not i in game.solved_fin_a.keys():
                game.solving_a = True
                game.solving_num = i
                game.solving_state = 1
                game.solving_start = self._frame_count
                game.solved_fin_a[i] = game.final.solved_a[i]
                self._sound_answer.play()
            if game.solving_a and game.solving_num == i:
                a,p = self.solve_answer(i, game, a, p)
            self.draw_answer(i, a, p) 
        #self.draw_points(game)
        
    def solve_answer(self, num, game, a, p):
        #a,p = game.get_round().answers[game.solving_num]
        if game.solving_state == self._alen:
            self._sound_points.play()
            game.solving = False
            game.solving_a = False
            game.solving_b = False
        else:
            p = "--"
        n = min(game.solving_state, len(a))
        m = game.solving_state - n
        s = "{}{}{}".format(a[:n], " "*m, "."*(self._alen - (n+m)))
        game.solving_state += ((self._frame_count - game.solving_start) % 5) // 4
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
    def __init__(self, q,r,x):
        self.game = None
        self._q = q
        self._r = r
        self._x = x

    def do(self,cmd):
        c = cmd.split("&")
        if c[0] == "load":
            self.game = Game()
            self.game.set_team_a("")
            self.game.set_team_b("")
            self.game.load(c[1])
            self._r.put("done")
        elif c[0] == "setround":
            self.game.set_round(int(c[1]))
            self._r.put(self.game.get_round().get_data())
        elif c[0] == "setfinal":
            self.game.set_final()
            self._r.put(self.game.final.get_data())
        elif c[0] == "solve":
            self.game.solve(int(c[1]))
            self._r.put("0")
        elif c[0] == "wrong":
            self.game.wrong()
            self._r.put("0")
        elif c[0] == "quit":
            self.running = False
            self._r.put("0")
            self._x.put("0")
        elif c[0] == "setteama":
            self.game.set_team_a(c[1])
            self._r.put(c[1])
        elif c[0] == "setteamb":
            self.game.set_team_b(c[1])
            self._r.put(c[1])
        elif c[0] == "pointstb":
            self.game.make_points(self.game.team_b)
            self._r.put("0")
        elif c[0] == "pointsta":
            self.game.make_points(self.game.team_a)
            self._r.put("0")
        elif c[0] == "setpointsa":
            self.game.team_a.points = int(c[1])
            self._r.put("0")
        elif c[0] == "setpointsb":
            self.game.team_b.points = int(c[1])
            self._r.put("0")

    def run(self):
        self.running = False
        while self._q.empty():
            time.sleep(0.1)
        if "init" in self._q.get():
            self.running = True
        
        
        r = Renderer()
        while not r.render(self.game) and self.running:
            if not self._q.empty():
                self.do(self._q.get())
        
        pygame.quit ()


def main():
    q = Queue()
    r = Queue()
    x = Queue()

    recvr = Process(target=srvr, args=(q,r,x))
    recvr.start()
    s = Session(q,r,x)
    s.run()
    r.put("stopit")
    recvr.join()

if __name__ == '__main__':
    main()
