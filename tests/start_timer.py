from stmpy import Driver, Machine
import logging


class Tick:

    def __init__(self):
        None

    def print(self, message):
        time = self.stm.get_timer('tick')
        #print(message)
        #print('remaining {}'.format(time))
        #print(self.stm.driver.print_status())




def test_tick():

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


test_tick()
