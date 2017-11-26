import time
import logging
from threading import Thread


def _current_time_millis():
    return int(round(time.time() * 1000))


class Scheduler:

    _stms_by_id = {}

    def __init__(self):
        logging.warning('init shceduler!')
        self._active = False
        self._event_queue = []
        self._timer_queue = []


    def add_stm(self, stm):
        stm._initialize(self)
        if stm.id is not None:
            # TODO warning when STM already registered
            Scheduler._stms_by_id[stm.id] = stm

    def start(self, max_transitions=None):
        """
        Add optional arguments max_millis stop after this timer
        max_transitions: execute only this number of transitions, then stop
        """
        self._active = True
        self._max_transitions = max_transitions
        # TODO start in a new thread?
        self.thread = Thread(target = self._start_loop)
        self.thread.start()

    def stop(self):
        self._active = False
        # TODO maybe some wakeup


    def wait_until_finished(self):
        self.thread.join()


    def _sort_timer_queue(self):
        self._timer_queue = sorted(self._timer_queue, key=lambda timer: timer['timeout_abs'])


    def _start_timer(self, timer_id, timeout, stm):
        timeout_abs = _current_time_millis() + int(timeout)
        self._timer_queue.append({'id': timer_id, 'timeout': timeout, 'timeout_abs': timeout_abs, 'stm': stm})
        self._sort_timer_queue()

    def _stop_timer(self, timer_id, stm):
        # TODO search through the timer queue and remove timer, sort again
        #_sort_timer_queue()
        pass

    def _add_event(self, event_id, data, stm):
        # add the event to the queue
        self._event_queue.append({'id': event_id, 'data': data, 'stm': stm})

    def send_event(self, stm_id, event_id, data=None):
        stm = Scheduler._stms_by_id[stm_id]
        # TODO error when STM not found
        self._add_event(event_id, data, stm)


    def _execute_transition(self, stm, id, data):
        stm._execute_event(id, data)
        if self._max_transitions is not None:
            print('checking max {}'.format(self._max_transitions))
            self._max_transitions = self._max_transitions-1
            if self._max_transitions == 0:
                self._active = False


    def _start_loop(self):

        while self._active:
            #print('Scheduler in queue')
            # check timer queue, if a timer expired
            if self._timer_queue:
                # timer queue is not empty
                timer = self._timer_queue[0]
                if timer['timeout_abs'] < _current_time_millis():
                    # the timer is expired
                    self._timer_queue.pop()
                    self._execute_transition(timer['stm'], timer['id'], None)

            # check event queues
            if self._event_queue:
                # event queue is not empty
                event = self._event_queue.pop()
                self._execute_transition(event['stm'], event['id'], event['data'])


            # TODO sleep for some time




        print('Scheduler finished')
