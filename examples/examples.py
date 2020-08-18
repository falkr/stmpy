from stmpy import Machine, Driver
import logging


class Tick:
    def __init__(self):
        self.ticks = 0
        self.tocks = 0

    def on_init(self):
        print("Init!")
        self.stm.start_timer("tick", 1000)

    def on_tick(self):
        print("Tick!")
        self.ticks = self.ticks + 1
        self.stm.start_timer("tock", 1000)
        print(self.stm.driver.print_status())
        self.stm.start_timer("tock", 1000)
        print(self.stm.driver.print_status())
        self.stm.stop_timer("tock")
        print(self.stm.driver.print_status())
        self.stm.start_timer("tock", 1000)

    def on_tock(self):
        print("Tock!")
        self.tocks = self.tocks + 1
        self.stm.start_timer("tick", 1000)


def test_tick():

    logger = logging.getLogger("stmpy.Driver")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    scheduler = Driver()
    tick = Tick()

    t0 = {"source": "initial", "target": "s_tick", "effect": "on_init"}
    t1 = {
        "trigger": "tick",
        "source": "s_tick",
        "target": "s_tock",
        "effect": "on_tick",
    }
    t2 = {
        "trigger": "tock",
        "source": "s_tock",
        "target": "s_tick",
        "effect": "on_tock",
    }

    stm_tick = Machine(name="stm_tick", transitions=[t0, t1, t2], obj=tick)

    # the object may need the stm to add events and control timers
    tick.stm = stm_tick

    scheduler.add_machine(stm_tick)
    scheduler.start(max_transitions=3)
    scheduler.wait_until_finished()


test_tick()


class Tick_2:
    def __init__(self):
        self.ticks = 0
        self.tocks = 0

    def on_init(self):
        print("Init!")
        self.stm.start_timer("tick", 1000)

    def on_tick(self):
        print("Tick!")
        self.ticks = self.ticks + 1
        self.stm.start_timer("tock", 1000)
        print(self.stm.driver.print_state())
        self.stm.start_timer("tock", 1000)
        print(self.stm.driver.print_state())
        self.stm.stop_timer("tock")
        print(self.stm.driver.print_state())
        self.stm.start_timer("tock", 1000)

    def on_tock(self):
        print("Tock!")
        self.tocks = self.tocks + 1
        self.stm.start_timer("tick", 1000)

    def t_1(self):
        self.on_tick()
        return "s_tock"

    def t_2(self):
        self.on_tock()
        return "s_tick"


def test_tick_2():

    logger = logging.getLogger("stmpy.Driver")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    scheduler = Driver()
    tick = Tick_2()

    t0 = {"source": "initial", "target": "s_tick", "effect": "on_init"}
    t1 = {"trigger": "tick", "source": "s_tick", "function": tick.t_1}
    t2 = {"trigger": "tock", "source": "s_tock", "function": tick.t_2}

    stm_tick = Machine(name="stm_tick", transitions=[t0, t1, t2], obj=tick)

    # the object may need the stm to add events and control timers
    tick.stm = stm_tick

    scheduler.add_stm(stm_tick)
    scheduler.start(max_transitions=10)
    scheduler.wait_until_finished()


# test_tick_2()


class Pong:
    def on_init(self):
        pass

    def on_timeout(self):
        self.stm.scheduler.send_signal("pong", "stm_ping")

    def on_ping(self):
        print("Ping!")
        self.stm.start_timer("t", 1000)


class Ping:
    def __init__(self):
        pass

    def on_init(self):
        print("Init Ping")
        self.stm.start_timer("t", 1000)

    def on_timeout(self):
        self.stm.scheduler.send_signal("ping", "stm_pong")

    def on_pong(self):
        print("Pong!")
        self.stm.start_timer("t", 1000)


def test_ping_pong():

    scheduler = Driver()

    ping = Ping()
    t0 = {"source": "initial", "target": "s_1", "effect": "on_init"}
    t1 = {"trigger": "t", "source": "s_1", "target": "s_2", "effect": "on_timeout"}
    t2 = {"trigger": "pong", "source": "s_2", "target": "s_1", "effect": "on_pong"}
    stm_ping = Machine(transitions=[t0, t1, t2], obj=ping, name="stm_ping")
    ping.stm = stm_ping

    pong = Pong()
    t0 = {"source": "initial", "target": "s_1"}
    t1 = {"trigger": "t", "source": "s_2", "target": "s_1", "effect": "on_timeout"}
    t2 = {"trigger": "ping", "source": "s_1", "target": "s_2", "effect": "on_ping"}
    stm_pong = Machine(transitions=[t0, t1, t2], obj=pong, name="stm_pong")
    pong.stm = stm_pong

    scheduler.add_stm(stm_ping)
    scheduler.add_stm(stm_pong)

    scheduler.step(4)
    scheduler.print_state()
    scheduler.step()
    scheduler.print_state()


# test_ping_pong()


class Busy:
    def __init__(self):
        self.count = 0

    def on_busy(self):
        self.count = self.count + 1
        print("Busy! {}".format(self.count))
        self.stm.send_signal("busy")


def test_busy():
    busy = Busy()
    t0 = {"source": "initial", "target": "s_busy", "effect": "on_busy"}
    t1 = {
        "trigger": "busy",
        "source": "s_busy",
        "target": "s_busy",
        "effect": "on_busy",
    }
    stm_busy = Machine(transitions=[t0, t1], obj=busy, name="stm_busy")
    busy.stm = stm_busy

    scheduler = Driver()
    scheduler.add_stm(stm_busy)
    scheduler.start(max_transitions=100)
    print("scheduler started")

    scheduler.wait_until_finished()


# test_busy()


def test_timer():
    if "s" is "s":
        print("same!")
    t0 = {"source": "initial", "target": "s_1"}
    m = Machine(transitions=[t0], obj=None, name="t")
    driver = Driver()
    driver.add_stm(m)
    m.start_timer("t", 1000)
    print(driver.print_status())
    m.stop_timer("t")
    print(driver.print_status())


# test_timer()


class Blink:
    def on(self):
        print("on")
        self.stm.start_timer("t", 1000)

    def off(self):
        print("off")
        self.stm.start_timer("t", 1000)


def test_blink():
    blink = Blink()
    t0 = {"source": "initial", "target": "blink_on", "effect": "on"}
    t1 = {"trigger": "t", "source": "blink_on", "target": "blink_off", "effect": "off"}
    t2 = {"trigger": "t", "source": "blink_off", "target": "blink_on", "effect": "on"}
    stm_blink = Machine(transitions=[t0, t1, t2], obj=blink, name="blink")
    blink.stm = stm_blink

    print(stm_blink.print_graph())

    scheduler = Driver()
    scheduler.add_stm(stm_blink)
    scheduler.start()
    print("scheduler started")

    scheduler.wait_until_finished()


# test_blink()
