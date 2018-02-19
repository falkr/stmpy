import unittest
import logging
from stmpy import Machine
from stmpy import Driver

# See https://docs.python.org/3/library/unittest.html


class Busy:

    def __init__(self):
        self.count = 0

    def on_busy(self):
        self.count = self.count + 1
        print('Busy! {}'.format(self.count))
        self.stm.send_signal('busy')


class BusyTestCase(unittest.TestCase):
    def setUp(self):
        logger = logging.getLogger('stmpy')
        logger.setLevel(logging.DEBUG)
        pass

    def tearDown(self):
        pass

    def test_busy(self):
        busy = Busy()
        t0 = {'source': 'initial', 'target': 's_busy', 'effect': 'on_busy'}
        t1 = {'trigger': 'busy', 'source': 's_busy',
              'target': 's_busy', 'effect': 'on_busy'}
        stm_busy = Machine(name='busy', transitions=[t0, t1], obj=busy)
        busy.stm = stm_busy

        scheduler = Driver()
        scheduler.add_stm(stm_busy)
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

    def setUp(self):
        print('setup two test case')
        pass

    def tearDown(self):
        pass

    def test_two(self):
        two = TwoMethods()
        t0 = {'source': 'initial', 'target': 's_1'}
        t1 = {'trigger': 't', 'source': 's_1', 'target': 's_2',
              'effect': 'm1;m2'}
        stm_two = Machine(name='stm_two', transitions=[t0, t1], obj=two)
        two.stm = stm_two

        scheduler = Driver()
        scheduler.add_stm(stm_two)
        scheduler.start(max_transitions=2)
        print('scheduler started')
        scheduler.send_signal('t', 'stm_two')

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

    def test_terminate(self):
        terminate = Terminate()
        t0 = {'source': 'initial', 'target': 's_1'}
        t1 = {'trigger': 't', 'source': 's_1', 'target': 's_2',
              'effect': 'action'}
        stm_terminate = Machine(name='stm_terminate', transitions=[t0, t1],
                                obj=terminate)
        terminate.stm = stm_terminate

        scheduler = Driver()
        scheduler.add_stm(stm_terminate)
        scheduler.start(max_transitions=2, keep_active=False)
        print('scheduler started')
        scheduler.send_signal('t', 'stm_terminate')

        scheduler.wait_until_finished()

        self.assertTrue(True)
