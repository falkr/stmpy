import time
import logging
from queue import Queue
from queue import Empty
from threading import Thread


def _current_time_millis():
    return int(round(time.time() * 1000))


class Driver:
    """
    A driver can run several machines.

    **Run-to-completion:**
    One driver contains one thread. Machines assigned to a driver are executed
    within this single thread. This provides a strict temporal ordering of
    behavior for state machines assigned to the same driver. A driver only
    executes one transition at a time, and always executes this transition to
    completion. This means that the action within a transition can access
    shared variables without interleaving behavior. One transition is always
    executed separate from all other transitions.
    """

    _stms_by_id = {}

    def __init__(self):
        """Create a new driver."""
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Logging works")
        self._active = False
        self._event_queue = Queue()
        self._timer_queue = []
        self._next_timeout = None
        # TODO need clarity if this should be a class variable
        Driver._stms_by_id = {}

    def _wake_queue(self):
        # Sends a None event to wake up the queue.
        self._event_queue.put(None)

    def print_status(self):
        """Provide a snapshot of the current status."""
        s = []
        s.append("=== State Machines: ===\n")
        for stm_id in Driver._stms_by_id:
            stm = Driver._stms_by_id[stm_id]
            s.append("    - {} in state {}\n".format(stm.id, stm.state))
        s.append("=== Events in Queue: ===\n")
        for event in self._event_queue.queue:
            if event is not None:
                s.append(
                    "    - {} for {} with args:{} kwargs:{}\n".format(
                        event["id"], event["stm"].id, event["args"], event["kwargs"]
                    )
                )
        s.append("=== Active Timers: {} ===\n".format(len(self._timer_queue)))
        for timer in self._timer_queue:
            s.append(
                "    - {} for {} with timeout {}\n".format(
                    timer["id"], timer["stm"].id, timer["timeout"]
                )
            )
        s.append("=== ================ ===\n")
        return "".join(s)

    def status(self):
        """Provide a snapshot of the current status.
        +------ Remaining steps: 023 ---------+
        | timers  -----> t1 (for stm_tick) 3000 ms
        |                t2 (for stm_tick) 3000 ms
        | (+ 3 more)     t3 (for stm_tick) 3000 ms
        +---------------------------------------
        | stm1: A     in state  s_01
        | Queue head --> A (saved)
        |                B
        |                C
        |                ... (+ 3 more)
        +---------------------------------------"""
        s = []
        s.append("=== State Machines: ===\n")
        for stm_id in Driver._stms_by_id:
            stm = Driver._stms_by_id[stm_id]
            s.append("    - {} in state {}\n".format(stm.id, stm.state))
        s.append("=== Events in Queue: ===\n")
        for event in self._event_queue.queue:
            if event is not None:
                s.append(
                    "    - {} for {} with args:{} kwargs:{}\n".format(
                        event["id"], event["stm"].id, event["args"], event["kwargs"]
                    )
                )
        s.append("=== Active Timers: {} ===\n".format(len(self._timer_queue)))
        for timer in self._timer_queue:
            s.append(
                "    - {} for {} with timeout {}\n".format(
                    timer["id"], timer["stm"].id, timer["timeout"]
                )
            )
        s.append("=== ================ ===\n")
        return "".join(s)

    def add_machine(self, machine):
        """Add the state machine to this driver."""
        self._logger.debug("Adding machine {} to driver".format(machine.id))
        machine._driver = self
        machine._reset()
        if machine.id is not None:
            # TODO warning when STM already registered
            Driver._stms_by_id[machine.id] = machine
            self._add_event(event_id=None, args=[], kwargs={}, stm=machine)

    def start(self, max_transitions=None, keep_active=False):
        """
        Start the driver.

        This method creates a thread which runs the event loop.
        The method returns immediately. To wait until the driver
        finishes, use `stmpy.Driver.wait_until_finished`.

        `max_transitions`: execute only this number of transitions, then stop
        `keep_active`: When true, keep the driver running even when all state
        machines terminated
        """
        self._active = True
        self._max_transitions = max_transitions
        self._keep_active = keep_active
        self.thread = Thread(target=self._start_loop)
        self.thread.start()

    def step(self, steps=1):
        """Execute a single step."""
        self.start(max_transitions=steps)
        self.wait_until_finished()

    def stop(self):
        """Stop the driver."""
        self._active = False
        self._wake_queue()

    def wait_until_finished(self):
        """Blocking method to wait until the driver finished its execution."""
        try:
            self.thread.join()
        except KeyboardInterrupt:
            self._logger.debug("Keyboard interrupt detected, stopping driver.")
            self._active = False
            self._wake_queue()

    def _sort_timer_queue(self):
        self._timer_queue = sorted(
            self._timer_queue, key=lambda timer: timer["timeout_abs"]
        )

    def _start_timer(self, name, timeout, stm):
        self._logger.debug("Start timer with name={} from stm={}".format(name, stm.id))
        timeout_abs = _current_time_millis() + int(timeout)
        self._stop_timer(name, stm, log=False)
        self._timer_queue.append(
            {
                "id": name,
                "timeout": timeout,
                "timeout_abs": timeout_abs,
                "stm": stm,
                "tid": stm.id + "_" + name,
            }
        )
        self._sort_timer_queue()
        self._wake_queue()

    def _stop_timer(self, name, stm, log=True):
        if log:
            self._logger.debug(
                "Stopping timer with name={} from stm={}".format(name, stm.id)
            )
        index = 0
        index_to_delete = None
        tid = stm.id + "_" + name
        for timer in self._timer_queue:
            if timer["tid"] == tid:
                index_to_delete = index
            index = index + 1
        if index_to_delete is not None:
            self._timer_queue.pop(index_to_delete)

    def _get_timer(self, name, stm):
        tid = stm.id + "_" + name
        for timer in self._timer_queue:
            if timer["tid"] == tid:
                return timer["timeout_abs"] - _current_time_millis()
        return None

    def _check_timers(self):
        """
        Check for expired timers.

        If there are any timers that expired, place them in the event
        queue.
        """
        if self._timer_queue:
            timer = self._timer_queue[0]
            if timer["timeout_abs"] < _current_time_millis():
                # the timer is expired, remove first element in queue
                self._timer_queue.pop(0)
                # put into the event queue
                self._logger.debug(
                    "Timer {} expired for stm {}, adding it to event queue.".format(
                        timer["id"], timer["stm"].id
                    )
                )
                self._add_event(timer["id"], [], {}, timer["stm"], front=True)
                # not necessary to set next timeout,
                # complete check timers will be called again
            else:
                self._next_timeout = (
                    timer["timeout_abs"] - _current_time_millis()
                ) / 1000
                if self._next_timeout < 0:
                    self._next_timeout = 0
        else:
            self._next_timeout = None

    def _add_event(self, event_id, args, kwargs, stm, front=False):
        if front:
            self._event_queue.queue.appendleft(
                {"id": event_id, "args": args, "kwargs": kwargs, "stm": stm}
            )
        else:
            self._event_queue.put(
                {"id": event_id, "args": args, "kwargs": kwargs, "stm": stm}
            )

    def send(self, message_id, stm_id, args=None, kwargs=None):
        """
        Send a message to a state machine handled by this driver.

        If you have a reference to the state machine, you can also send it
        directly to it by using `stmpy.Machine.send`.

        `stm_id` must be the id of a state machine earlier added to the driver.
        """
        if args == None:
            args = []
        if kwargs == None:
            kwargs = {}
        if stm_id not in Driver._stms_by_id:
            self._logger.warn(
                "Machine with name {} cannot be found. "
                "Ignoring message {}.".format(stm_id, message_id)
            )
        else:
            stm = Driver._stms_by_id[stm_id]
            self._add_event(message_id, args, kwargs, stm)

    def _terminate_stm(self, stm_id):
        self._logger.debug("Terminating machine {}.".format(stm_id))
        # removing it from the table of machines
        Driver._stms_by_id.pop(stm_id, None)
        if not self._keep_active and not Driver._stms_by_id:
            self._logger.debug("No machines anymore, stopping driver.")
            self._active = False
            self._wake_queue()

    def _execute_transition(self, stm, event_id, args, kwargs, event):
        if stm._defers_event(event_id):
            stm._add_to_defer_queue(event)
            self._logger.debug(
                "Machine {} defers event {} in state {}".format(
                    stm._id, event_id, stm._state
                )
            )
            return
        stm._execute_transition(event_id, args, kwargs)
        if self._max_transitions is not None:
            self._max_transitions = self._max_transitions - 1
            if self._max_transitions == 0:
                self._logger.debug("Stopping driver because max_transitions reached.")
                self._active = False

    def _start_loop(self):
        self._logger.debug("Starting loop of the driver.")
        while self._active:
            self._check_timers()
            try:
                event = self._event_queue.get(block=True, timeout=(self._next_timeout))
                if event is not None:
                    # (None events are just used to wake up the queue.)
                    self._execute_transition(
                        stm=event["stm"],
                        event_id=event["id"],
                        args=event["args"],
                        kwargs=event["kwargs"],
                        event=event,
                    )
            except Empty:
                # timeout has occured
                self._logger.debug("Timer expired, driver loop active again.")
            except KeyboardInterrupt:
                self.active = False
                self._logger.debug("Keyboard interrupt. Stopping the driver.")
        self._logger.debug("Driver loop is finished.")
