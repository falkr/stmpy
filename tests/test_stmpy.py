import unittest
from stmpy import StateMachine
from stmpy import Scheduler

# See https://docs.python.org/3/library/unittest.html


class Busy:

    def __init__(self):
        self.count = 0

    def on_busy(self):
        self.count = self.count + 1
        print('Busy! {}'.format(self.count))
        print('Busy!')
        self.stm.send_signal('busy')


class BusyTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_busy(self):
        busy = Busy()
        t = {'trigger':'busy', 'source':'s_busy', 'target':'s_busy', 'effect':'on_busy'}
        stm_busy = StateMachine(first_state='s_busy', transitions=[t], obj=busy, stm_id='stm_busy', initial_effects='on_busy')
        busy.stm = stm_busy

        scheduler = Scheduler()
        scheduler.add_stm(stm_busy)
        scheduler.start(max_transitions=5)
        print('scheduler started')

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
        t = {'trigger':'t', 'source':'s_1', 'target':'s_2', 'effect':'m1 m2'}
        stm_two = StateMachine(first_state='s_1', transitions=[t], obj=two, stm_id='stm_two')
        two.stm = stm_two

        scheduler = Scheduler()
        scheduler.add_stm(stm_two)
        scheduler.start(max_transitions=1)
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
        t = {'trigger':'t', 'source':'s_1', 'target':'s_2', 'effect':'action'}
        stm_terminate = StateMachine(first_state='s_1', transitions=[t], obj=terminate, stm_id='stm_terminate')
        terminate.stm = stm_terminate

        scheduler = Scheduler()
        scheduler.add_stm(stm_terminate)
        scheduler.start(max_transitions=2, block=False, keep_active=False)
        print('scheduler started')
        scheduler.send_signal('t', 'stm_terminate')

        scheduler.wait_until_finished()

        self.assertTrue(True)
