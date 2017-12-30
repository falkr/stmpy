import time
import logging
from threading import Thread
from threading import Event
from threading import Condition
from queue import Queue
from queue import Empty


def _current_time_millis():
    return int(round(time.time() * 1000))

class IterableQueue():
    def __init__(self,source_queue):
            self.source_queue = source_queue
    def __iter__(self):
        while True:
            try:
               yield self.source_queue.get_nowait()
            except Empty:
               return


class Scheduler:

    _stms_by_id = {}

    def __init__(self):
        #logging.setLevel
        logging.warning('init scheduler!')
        self._active = False
        self._event_queue = Queue()
        self._timer_queue = []
        self._next_timeout = None
        # TODO need clarity of this should be a class variable
        Scheduler._stms_by_id = {}


    def print_state(self):
        print('=== State Machines: ===')
        for stm_id in Scheduler._stms_by_id:
            stm = Scheduler._stms_by_id[stm_id]
            print('    - {} in state {}'.format(stm.id, stm.state))
        print('=== Events in Queue: ===')
        #print('Queue: {}'.format(self._event_queue))
        for event in IterableQueue(self._event_queue):
            if event is not None:
                print('    - {} for {} with args:{} kwargs:{}'.format(event['id'], event['stm'].id, event['args'], event['kwargs']))
        print('=== Active Timers: ===')
        for timer in self._timer_queue:
            print('    - {} for {} with timeout {}'.format(timer['id'], timer['stm'].id, timer['timeout']))

    def add_stm(self, stm):
        """
        Add the state machine to this scheduler.
        """
        print("Add and initialize stm={}".format(stm))
        #stm._initialize(self)
        stm._scheduler = self
        if stm.id is not None:
            # TODO warning when STM already registered
            Scheduler._stms_by_id[stm.id] = stm
            self._event_queue.put({'id': None, 'stm': stm, 'args': [], 'kwargs': {}})

    def start(self, max_transitions=None, keep_active=False):
        """
        max_transitions: execute only this number of transitions, then stop
        keep_active: When true, keep the scheduler running even when all state machines terminated
        """
        self._active = True
        self._max_transitions = max_transitions
        self._keep_active = keep_active
        self.thread = Thread(target = self._start_loop)
        self.thread.start()


    def step(self, steps=1):
        self.start(max_transitions=steps, block=True)


    def stop(self):
        self._active = False
        self._event_queue.put(None) # wake up the thread


    def wait_until_finished(self):
        try:
            self.thread.join()
        except KeyboardInterrupt:
            print('Scheduler aborted by keyboard.')
            self._active = False


    def _sort_timer_queue(self):
        self._timer_queue = sorted(self._timer_queue, key=lambda timer: timer['timeout_abs'])


    def _start_timer(self, timer_id, timeout, stm):
        print("Start timer with id={} from stm={}".format(timer_id, stm))
        timeout_abs = _current_time_millis() + int(timeout)
        self._timer_queue.append({'id': timer_id, 'timeout': timeout, 'timeout_abs': timeout_abs, 'stm': stm})
        self._sort_timer_queue()
        self._event_queue.put(None) # wake up the thread

    def _stop_timer(self, timer_id, stm):
        # TODO search through the timer queue and remove timer, sort again
        #_sort_timer_queue()
        self._event_queue.put(None) # wake up the thread

    def _check_timers(self):
        if self._timer_queue:
            timer = self._timer_queue[0]
            if timer['timeout_abs'] < _current_time_millis():
                # the timer is expired
                self._timer_queue.pop()
                # put into the event queue
                # TODO maybe put timer first in queue?
                self._event_queue.put({'id': timer['id'], 'args': [], 'kwargs': {}, 'stm': timer['stm']})
                # not necessary to set next timeout, complete check timers will be called again
            else:
                self._next_timeout = (timer['timeout_abs'] -  _current_time_millis()) / 1000
                if self._next_timeout<0:
                    self._next_timeout = 0
        else:
            self._next_timeout = None


    def _add_event(self, event_id, args, kwargs, stm):
        # add the event to the queue
        self._event_queue.put({'id': event_id, 'args': args, 'kwargs':kwargs, 'stm': stm})


    def send_signal(self, signal_id, stm_id, args=[], kwargs={}):
        """
        Send a signal to a state machine handled by this scheduler. If you have
        a reference to the state machine, you can also send it directly to it by
        using StateMachine.send_signal().

        `stm_id` must be the id of a state machine earlier added to the scheduler.
        """
        stm = Scheduler._stms_by_id[stm_id]
        # TODO error when STM not found
        self._add_event(signal_id, args, kwargs, stm)


    def _terminate_stm(self, stm_id):
        # remove the state machine
        logging.warning('terminating stm with frnk id {}'.format(stm_id))
        Scheduler._stms_by_id.pop(stm_id, None)
        if not self._keep_active:
            if not Scheduler._stms_by_id:
                self._active = False
                self._event_queue.put(None) # wake up the thread


    def _execute_transition(self, stm, event_id, args, kwargs):
        stm._execute_transition(event_id, args, kwargs)
        if self._max_transitions is not None:
            self._max_transitions = self._max_transitions-1
            if self._max_transitions == 0:
                self._active = False


    def _start_loop(self):

        while self._active:
            #print('Scheduler in queue')
            # check timer queue, if a timer expired
            self._check_timers()
            try:
                #print("Wait for next event, {} sec max.".format(self._next_timeout))
                event = self._event_queue.get(block=True, timeout=(self._next_timeout))
                if event is None:
                    # somebody added a timer, or shutdown the scheduler
                    pass
                else:
                    self._execute_transition(stm=event['stm'], event_id=event['id'], args=event['args'], kwargs=event['kwargs'])
                    if not Scheduler._stms_by_id and not self._keep_active: # no more state machines
                        self._active = False
            except Empty:
                # timeout has occured
                print("Event queue interrupted waiting because of timeout")
            except KeyboardInterrupt:
                self.active = False
                print("Scheduler aborted.")

        print('Scheduler finished')
