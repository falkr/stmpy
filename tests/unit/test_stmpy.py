
from tests import *
from tests.helpers import *

import unittest
import logging
from stmpy import Machine
from stmpy import Driver
import stmpy


class Busy:

    def __init__(self):
        self.count = 0

    def on_busy(self):
        self.count = self.count + 1
        print('Busy! {}'.format(self.count))
        self.stm.send('busy')


class BusyTestCase(unittest.TestCase):
    
    def setUp(self):
        logger = logging.getLogger('stmpy')
        logger.setLevel(logging.DEBUG)
        pass

    def test(self):
        busy = Busy()
        t0 = {'source': 'initial', 'target': 's_busy', 'effect': 'on_busy'}
        t1 = {'trigger': 'busy', 'source': 's_busy',
              'target': 's_busy', 'effect': 'on_busy'}
        stm_busy = Machine(name='busy', transitions=[t0, t1], obj=busy)
        busy.stm = stm_busy

        scheduler = Driver()
        scheduler.add_machine(stm_busy)
        scheduler.start(max_transitions=5)
        scheduler.wait_until_finished()

        self.assertTrue(True)

class TwoMethods:

    def __init__(self):
        self.count = 0

    def m1(self):
        self.count = self.count + 1
        print('m1 called {}'.format(self.count))

    def m2(self):
        self.count = self.count + 1
        print('m2 called {}'.format(self.count))


class TwoMethodsTestCase(unittest.TestCase):

    def test(self):
        two = TwoMethods()
        t0 = {'source': 'initial', 'target': 's_1'}
        t1 = {'trigger': 't', 'source': 's_1', 'target': 's_2',
              'effect': 'm1;m2'}
        stm_two = Machine(name='stm_two', transitions=[t0, t1], obj=two)
        two.stm = stm_two

        scheduler = Driver()
        scheduler.add_machine(stm_two)
        scheduler.start(max_transitions=2)
        print('scheduler started')
        scheduler.send('t', 'stm_two')

        scheduler.wait_until_finished()

        self.assertTrue(True)


class Terminate:

    def action(self):
        print('action')
        self.stm.terminate()


class TerminateTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test(self):
        terminate = Terminate()
        t0 = {'source': 'initial', 'target': 's_1'}
        t1 = {'trigger': 't', 'source': 's_1', 'target': 's_2',
              'effect': 'action'}
        stm_terminate = Machine(name='stm_terminate', transitions=[t0, t1],
                                obj=terminate)
        terminate.stm = stm_terminate

        scheduler = Driver()
        scheduler.add_machine(stm_terminate)
        scheduler.start(max_transitions=2, keep_active=False)
        scheduler.send('t', 'stm_terminate')

        scheduler.wait_until_finished()

        _ = stmpy.get_graphviz_dot(stm_terminate)
        _ = scheduler.print_status()

        self.assertTrue(True)

    
class DeferTestCase(unittest.TestCase):

    def test(self):
        print(__name__)
        debug_level = logging.DEBUG
        logger = logging.getLogger(__name__)
        logger.setLevel(debug_level)
        ch = logging.StreamHandler()
        ch.setLevel(debug_level)
        formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        #terminate = Terminate()
        t0 = {'source': 'initial', 'target': 's1'}
        t1 = {'trigger': 'b', 'source': 's1', 'target': 's2'}
        t2 = {'trigger': 'a', 'source': 's2', 'target': 'final'}
        s1 = {'name': 's1', 'a': 'defer', 'a2': 'defer', 'a3': 'defer'}
        s2 = {'name': 's2', 'a2': 'defer', 'a3': 'defer'}

        stm_terminate = Machine(name='stm', transitions=[t0, t1, t2], states=[s1, s2], obj=None)
        #terminate.stm = stm_terminate

        _ = stmpy.get_graphviz_dot(stm_terminate)
        print(_)

        def unwrap(queue):
            s = []
            if queue is None: 
                return s
            for event in queue:
                if event is not None:
                    s.append(event['id'])
            return s
        

        driver = Driver()
        driver.add_machine(stm_terminate)
        driver.start(max_transitions=30, keep_active=False)
        driver.send('a', 'stm')
        driver.send('a2', 'stm')
        driver.send('a3', 'stm')

        print('Events {}'.format(unwrap(driver._event_queue.queue)))
        print(stm_terminate.state)
        print('Defers {}'.format(unwrap(stm_terminate._defer_queue)))
        print(driver._max_transitions)

        driver.send('b', 'stm')

        print('Events {}'.format(unwrap(driver._event_queue.queue)))
        print(stm_terminate.state)
        print('Defers {}'.format(unwrap(stm_terminate._defer_queue)))
        print(driver._max_transitions)

        driver.wait_until_finished()
        print(stm_terminate.state)
        self.assertTrue(True)


class Tick:

    def __init__(self):
        pass

    def print(self, message):
        _ = self.stm.get_timer('tick')
        #print(message)
        #print('remaining {}'.format(time))
        #print(self.stm.driver.print_status())


class TestTick(unittest.TestCase):

    def test(self):

        #print(stmpy.__version__)

        logger = logging.getLogger('stmpy')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)



        tick1 = Tick()
        t0 = {'source': 'initial',
            'target': 'active',
            'effect': 'start_timer("tick", 1000); print("initial1")'}
            #'effect': 'print("initial1")'}
        t1 = {'trigger': 'tick',
            'source': 'active',
            'target': 'active',
            'effect': 'start_timer("tick", 1000); print("timeout1")'}
            #'effect': 'print("timeout1")'}
        stm_tick_1 = Machine(name='stm_tick_1', transitions=[t0, t1], obj=tick1)
        tick1.stm = stm_tick_1

        tick2 = Tick()
        t0 = {'source': 'initial',
            'target': 'active',
            'effect': 'start_timer("tick", 2000); print("initial2")'}
            #'effect': 'print("initial2")'}
        t1 = {'trigger': 'tick',
            'source': 'active',
            'target': 'active',
            #'effect': 'print("timeout2")'}
            'effect': 'start_timer("tick", 1000); print("timeout2")'}
        stm_tick_2 = Machine(name='stm_tick_2', transitions=[t0, t1], obj=tick2)
        tick2.stm = stm_tick_2

        driver1 = Driver()

        driver1.start(max_transitions=6, keep_active=True)

        print('driver state: active {} and thread alive {} '.format(driver1._active, driver1.thread.is_alive()))

        driver1.add_machine(stm_tick_1)
        print(driver1.print_status())
        driver1.add_machine(stm_tick_2)
        print(driver1.print_status())
        driver1._wake_queue()
        print('driver state: active {} and thread alive {} '.format(driver1._active, driver1.thread.is_alive()))
        #driver1.start(max_transitions=6, keep_active=True)
        print(driver1.print_status())

        #driver2 = Driver()
        #driver1.add_machine(stm_tick_2)
        #driver2.start(max_transitions=10)

        driver1.wait_until_finished()

class EntryExitSelfLogic:

        def __init__(self):
            self.list = []

        def add(self, x):
            self.list.append(x)

        def do_action(self, x):
            self.list.append(x)

class EntryExitSelf(unittest.TestCase):

    def test(self):
        tick1 = EntryExitSelfLogic()
        t0 = {'source': 'initial', 'target': 's1'}
        t1 = {'trigger': 'b', 'source': 's1', 'target': 's1', 'effect': 'add("b")'}
        t2 = {'trigger': 'c', 'source': 's1', 'target': 'final', 'effect': 'add("c")'}

        s1 = {'name': 's1', 'a': 'add("a")', 'entry': 'add("entry")', 'exit': 'add("exit")'}

        stm = Machine(name='stm', transitions=[t0, t1, t2], states=[s1], obj=tick1)
        tick1.stm = stm

        _ = stmpy.get_graphviz_dot(stm)

        driver = Driver()
        driver.add_machine(stm)
        driver.start(max_transitions=30, keep_active=False)
        driver.send('a', 'stm')
        driver.send('b', 'stm')
        driver.send('c', 'stm')

        driver.wait_until_finished()


class StartStopTimer(unittest.TestCase):

    def test(self):
        t0 = {'source': 'initial', 'target': 's1', 'effect': 'start_timer("t1", "1000")'}
        t1 = {'trigger': 'a', 'source': 's1', 'target': 's1', 'effect': 'stop_timer("t1")'}
        t2 = {'trigger': 'b', 'source': 's1', 'target': 'final'}

        stm = Machine(name='stm', transitions=[t0, t1, t2], obj=None)

        _ = stmpy.get_graphviz_dot(stm)

        driver = Driver()
        driver.add_machine(stm)
        driver.start(keep_active=False)
        driver.send('a', 'stm')
        driver.send('b', 'stm')

        driver.wait_until_finished()


class CompoundTransition(unittest.TestCase):

    def compound(self, arg1, b1=None):
        return 'final'

    def test(self):
        t0 = {'source': 'initial', 'target': 's1'}
        t1 = {'trigger': 'a', 'source': 's1', 'function': self.compound, 'targets': 'final'}

        stm = Machine(name='stm', transitions=[t0, t1], obj=None)

        _ = stmpy.get_graphviz_dot(stm)

        driver = Driver()
        driver.add_machine(stm)
        driver.start(keep_active=False)
        driver.send('a', 'stm', args=['hi'], kwargs={'b1': 'bbb'})

        driver.wait_until_finished()

class CompoundFunctionContainer:

    def __init__(self, counter):
        self.counter = counter
    
    def compound(self, arg1, b1=None):
        print('_______________________________{}'.format(self.counter))
        if self.counter > 13:
            return 's2'
        return 's3'

class CompoundTransition_2(unittest.TestCase):

    def test(self):

        cfc = CompoundFunctionContainer(13)

        t0 = {'source': 'initial', 'target': 's1'}
        t1 = {'trigger': 'a', 'source': 's1', 'function': cfc.compound, 'targets': 's2 s3'}
        t2 = {'trigger': 'b', 'source': 's2', 'target': 'final'}
        t3 = {'trigger': 'b', 'source': 's3', 'target': 'final'}

        stm = Machine(name='stm', transitions=[t0, t1, t2, t3], obj=None)

        _ = stmpy.get_graphviz_dot(stm)

        driver = Driver()
        driver.add_machine(stm)
        driver.start(keep_active=False)
        driver.send('a', 'stm', args=['hi'], kwargs={'b1': 'bbb'})
        driver.send('b', 'stm')

        driver.wait_until_finished()


class DoAction(unittest.TestCase):

    def test(self):
        tick1 = EntryExitSelfLogic()
        t0 = {'source': 'initial', 'target': 's1'}
        t1 = {'trigger': 'b', 'source': 's1', 'target': 's1', 'effect': 'add("b")'}
        t2 = {'trigger': 'done', 'source': 's1', 'target': 'final', 'effect': 'add("c")'}

        s1 = {'name': 's1', 'do': 'do_action("a")'}

        stm = Machine(name='stm', transitions=[t0, t1, t2], states=[s1], obj=tick1)
        tick1.stm = stm

        _ = stmpy.get_graphviz_dot(stm)

        driver = Driver()
        driver.add_machine(stm)
        driver.start()

        driver.wait_until_finished()
