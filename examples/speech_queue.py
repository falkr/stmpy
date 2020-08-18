from stmpy import Machine
from stmpy import Driver
import stmpy
import logging
from os import system


class Speaker:
    def speak(self, string):
        print(string)
        system("say {}".format(string))


debug_level = logging.DEBUG
logger = logging.getLogger("stmpy")
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter(
    "%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)


print(stmpy.__version__)
speaker = Speaker()

t0 = {"source": "initial", "target": "ready"}
t1 = {"trigger": "speak", "source": "ready", "target": "speaking"}
t2 = {"trigger": "done", "source": "speaking", "target": "ready"}

s1 = {"name": "speaking", "do": "speak(*)", "speak": "defer"}

stm = Machine(name="stm", transitions=[t0, t1, t2], states=[s1], obj=speaker)
speaker.stm = stm

driver = Driver()
driver.add_machine(stm)
driver.start()

driver.send("speak", "stm", args=["My first sentence."])
driver.send("speak", "stm", args=["My second sentence."])
driver.send("speak", "stm", args=["My third sentence."])
driver.send("speak", "stm", args=["My fourth sentence."])

driver.wait_until_finished()
