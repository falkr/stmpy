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

    t1 = {'event':'tick', 'source':'s_tick', 'target':'s_tock', 'effect':'on_tick'}
    t2 = {'event':'tock', 'source':'s_tock', 'target':'s_tick', 'effect':'on_tock'}

    stm_tick = StateMachine(state='s_tick', transitions=[t1, t2], obj=tick, id='stm_tick', initial='on_init')

    # the object may need the stm to add events and control timers
    tick.stm = stm_tick

    scheduler.add_stm(stm_tick)
    scheduler.start(max_transitions=5)
    scheduler.wait_until_finished()



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
        self.stm.scheduler.send_event('stm_pong', 'ping')

    def on_pong(self):
        print('Pong!')
        self.stm.start_timer('t', 1000)


def test_ping_pong():

    scheduler = Scheduler()

    ping = Ping()
    t1 = {'event':'t',    'source':'s_1', 'target':'s_2', 'effect':'on_timeout'}
    t2 = {'event':'pong', 'source':'s_2', 'target':'s_1', 'effect':'on_pong'}
    stm_ping = StateMachine(state='s_1', transitions=[t1, t2], obj=ping, id='stm_ping', initial='on_init')
    ping.stm = stm_ping

    pong = Pong()
    t1 = {'event':'t',    'source':'s_2', 'target':'s_1', 'effect':'on_timeout'}
    t2 = {'event':'ping', 'source':'s_1', 'target':'s_2', 'effect':'on_ping'}
    stm_pong = StateMachine(state='s_1', transitions=[t1, t2], obj=pong, id='stm_pong')
    pong.stm = stm_pong

    scheduler.add_stm(stm_ping)
    scheduler.add_stm(stm_pong)
    scheduler.start(max_transitions=10)
    print('scheduler started')

    scheduler.wait_until_finished()




test_ping_pong()
