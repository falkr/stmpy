from stmpy import StateMachine
from stmpy import Scheduler


class Tick:

    def __init__(self):
        self.ticks = 0
        self.tocks = 0

    def on_init(self):
        print('Init!')
        self.stm.start_timer('tick', 1000)

    def on_tick(self):
        print('Tick!')
        self.ticks = self.ticks + 1
        self.stm.start_timer('tock', 1000)

    def on_tock(self):
        print('Tock!')
        self.tocks = self.tocks + 1
        self.stm.start_timer('tick', 1000)


def test_tick():

    scheduler = Scheduler()
    tick = Tick()

    t1 = {'trigger':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick'}
    t2 = {'trigger':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock'}

    stm_tick = StateMachine(state='s_tick', transitions=[t1, t2], obj=tick, id='stm_tick', initial='on_init')

    # the object may need the stm to add events and control timers
    tick.stm = stm_tick

    scheduler.add_stm(stm_tick)
    scheduler.start(max_transitions=50)
    scheduler.wait_until_finished()

#test_tick()

class Pong:

    def on_init(self):
        pass

    def on_timeout(self):
        self.stm.scheduler.send_event('stm_ping', 'pong')

    def on_ping(self):
        print('Ping!')
        self.stm.start_timer('t', 1000)


class Ping:

    def __init__(self):
        pass

    def on_init(self):
        print('Init Ping')
        self.stm.start_timer('t', 1000)

    def on_timeout(self):
        self.stm.send_signal('stm_pong', 'ping')

    def on_pong(self):
        print('Pong!')
        self.stm.start_timer('t', 1000)


def test_ping_pong():

    scheduler = Scheduler()

    ping = Ping()
    t1 = {'trigger':'t',    'source':'s_1', 'target':'s_2', 'effect':'on_timeout'}
    t2 = {'trigger':'pong', 'source':'s_2', 'target':'s_1', 'effect':'on_pong'}
    stm_ping = StateMachine(state='s_1', transitions=[t1, t2], obj=ping, id='stm_ping', initial='on_init')
    ping.stm = stm_ping

    pong = Pong()
    t1 = {'trigger':'t',    'source':'s_2', 'target':'s_1', 'effect':'on_timeout'}
    t2 = {'trigger':'ping', 'source':'s_1', 'target':'s_2', 'effect':'on_ping'}
    stm_pong = StateMachine(state='s_1', transitions=[t1, t2], obj=pong, id='stm_pong')
    pong.stm = stm_pong

    scheduler.add_stm(stm_ping)
    scheduler.add_stm(stm_pong)
    scheduler.start(max_transitions=100)
    print('scheduler started')

    scheduler.wait_until_finished()

#test_ping_pong()


class Busy:

    def __init__(self):
        self.count = 0

    def on_busy(self):
        self.count = self.count + 1
        print('Busy! {}'.format(self.count))
        print('Busy!')
        self.stm.send_signal('busy')


def test_busy():
    busy = Busy()
    t = {'trigger':'busy', 'source':'s_busy', 'target':'s_busy', 'effect':'on_busy'}
    stm_busy = StateMachine(state='s_busy', transitions=[t], obj=busy, id='stm_busy', initial='on_busy')
    busy.stm = stm_busy

    scheduler = Scheduler()
    scheduler.add_stm(stm_busy)
    scheduler.start(max_transitions=100)
    print('scheduler started')

    scheduler.wait_until_finished()



#test_busy()

import tkinter as tk
from PIL import ImageTk, Image

def callback():
    print("click!")


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.frank_root = master
        self.create_widgets()


    def create_widgets(self):
        #self.hi_there = tk.Button(self)
        #self.hi_there["text"] = "Hello World\n(click me)"
        #self.hi_there["command"] = self.say_hi
        #self.hi_there.pack(side="top")

        #self.quit = tk.Button(self, text="QUIT", fg="red", command=self.frank_root.destroy)
        #self.quit.pack(side="bottom")

        self.panel = tk.Label(self.frank_root, image = ImageTk.PhotoImage(Image.open("red_on.gif")))
        self.panel.pack(side = "bottom", fill = "both", expand = "yes")

        #Label(image=logo).grid()
    def say_hi(self):
        print("hi there, everyone!")



def test_button():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()


def test_image():
    root = tk.Tk()
    img = ImageTk.PhotoImage(Image.open("red_on.gif"))
    panel = tk.Label(root, image = img)
    panel.pack(side = "bottom", fill = "both", expand = "yes")
    root.mainloop()

test_button()
#test_image()
