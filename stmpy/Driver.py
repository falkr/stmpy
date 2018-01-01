import time
import logging
from threading import Thread
from threading import Event
from threading import Condition
from queue import Queue
from queue import Empty


def _current_time_millis():
    return int(round(time.time() * 1000))

class _IterableQueue():
    def __init__(self,source_queue):
            self.source_queue = source_queue
    def __iter__(self):
        while True:
            try:
               yield self.source_queue.get_nowait()
            except Empty:
               return


class Driver:

    _stms_by_id = {}

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.debug('Logging works')
        self._active = False
        self._event_queue = Queue()
        self._timer_queue = []
        self._next_timeout = None
        # TODO need clarity if this should be a class variable
        Driver._stms_by_id = {}


    def _wake_queue(self):
        # Sends a None event to wake up the queue.
        self._event_queue.put(None)


    def print_state(self):
        l = []
        l.append('=== State Machines: ===')
        for stm_id in Driver._stms_by_id:
            stm = Driver._stms_by_id[stm_id]
            l.append('    - {} in state {}'.format(stm.id, stm.state))
        l.append('=== Events in Queue: ===')
        for event in _IterableQueue(self._event_queue):
            if event is not None:
                l.append('    - {} for {} with args:{} kwargs:{}'.format(event['id'], event['stm'].id, event['args'], event['kwargs']))
        l.append('=== Active Timers: ===')
        for timer in self._timer_queue:
            l.append('    - {} for {} with timeout {}'.format(timer['id'], timer['stm'].id, timer['timeout']))
        return ''.join(l)


    def add_stm(self, stm):
        """
        Add the state machine to this driver.
        """
        stm._driver = self
        if stm.id is not None:
            # TODO warning when STM already registered
            Driver._stms_by_id[stm.id] = stm
            self._event_queue.put({'id': None, 'stm': stm, 'args': [], 'kwargs': {}})


    def start(self, max_transitions=None, keep_active=False):
        """
        Start the driver. This method creates a thread which runs the event
        loop. The method returns immediately. To wait until the driver
        finishes, use `stmpy.Driver.wait_until_finished`.

        `max_transitions`: execute only this number of transitions, then stop
        `keep_active`: When true, keep the driver running even when all state machines terminated
        """
        self._active = True
        self._max_transitions = max_transitions
        self._keep_active = keep_active
        self.thread = Thread(target = self._start_loop)
        self.thread.start()


    def step(self, steps=1):
        self.start(max_transitions=steps)
        self.wait_until_finished()


    def stop(self):
        self._active = False
        self._wake_queue()


    def wait_until_finished(self):
        try:
            self.thread.join()
        except KeyboardInterrupt:
            self._logger.debug('Keyboard interrupt detected, stopping driver.')
            self._active = False


    def _sort_timer_queue(self):
        self._timer_queue = sorted(self._timer_queue, key=lambda timer: timer['timeout_abs'])


    def _start_timer(self, timer_id, timeout, stm):
        self._logger.debug('Start timer with id={} from stm={}'.format(timer_id, stm))
        timeout_abs = _current_time_millis() + int(timeout)
        self._timer_queue.append({'id': timer_id, 'timeout': timeout, 'timeout_abs': timeout_abs, 'stm': stm})
        self._sort_timer_queue()
        self._wake_queue()


    def _stop_timer(self, timer_id, stm):
        self._logger.debug('Stopping timer with id={} from stm={}'.format(timer_id, stm))
        # TODO search through the timer queue and remove timer, sort again
        #_sort_timer_queue()
        self._wake_queue()


    def _check_timers(self):
        """
        Check if there are any timers that expired and place them in the event
        queue.
        """
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
        Send a signal to a state machine handled by this driver. If you have
        a reference to the state machine, you can also send it directly to it by
        using Machine.send_signal().

        `stm_id` must be the id of a state machine earlier added to the driver.
        """
        stm = Driver._stms_by_id[stm_id]
        if stm is None:
            self._logger.warn('Machine with name {} cannot be found. Ignoring signal {}.'.format(stm_id, event_id))
        else:
            self._add_event(signal_id, args, kwargs, stm)


    def _terminate_stm(self, stm_id):
        self._logger.debug('Terminating machine {}.'.format(stm_id))
        # removing it from the table of machines
        Driver._stms_by_id.pop(stm_id, None)
        if not self._keep_active and not Driver._stms_by_id:
            self._logger.debug('No machines anymore, stopping driver.')
            self._active = False
            self._event_queue.put(None) # wake up the thread


    def _execute_transition(self, stm, event_id, args, kwargs):
        self._logger.debug('Executing a transition.')
        stm._execute_transition(event_id, args, kwargs)
        if self._max_transitions is not None:
            self._max_transitions = self._max_transitions-1
            if self._max_transitions == 0:
                self._active = False


    def _start_loop(self):
        while self._active:
            self._logger.debug('Starting loop of the driver.')
            self._check_timers()
            try:
                event = self._event_queue.get(block=True, timeout=(self._next_timeout))
                if event is not None: # (None events are just used to wake up the queue.)
                    self._execute_transition(stm=event['stm'], event_id=event['id'], args=event['args'], kwargs=event['kwargs'])
            except Empty:
                # timeout has occured
                self._logger.debug('Timer expired, driver loop active again.')
            except KeyboardInterrupt:
                self.active = False
                self._logger.debug('Keyboard interrupt. Stopping the driver.')
        self._logger.debug('Driver loop is finished.')
