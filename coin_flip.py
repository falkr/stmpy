from stmpy import Machine, Driver

import ipywidgets as widgets
from IPython.display import display

class CoinFlip:

    def on_button_flip(self, b):
        self.stm.send_signal('flip') # <---- here we send a signal

    def __init__(self):
        # display the user interface
        # a button
        self.button_flip = widgets.Button(description="Flip")
        self.button_flip.on_click(self.on_button_flip)

        # text field
        self.text = widgets.Text(value='', placeholder='', description='String:', disabled=False)
        display(self.text, self.button_flip)

    def on_spinning(self):
        self.text.set_trait(name='value', value='spinning...')

    def on_heads(self):
        self.text.set_trait(name='value', value='Heads!')

    def on_tails(self):
        self.text.set_trait(name='value', value='Tails!')

    def flip_compound_transition(self):
        return 'head'

    def start_timer(self):
        # start the timer
        self.stm.start_timer('t', 1000)

coin_flip = CoinFlip()

# initial transition
t0 = {'source': 'initial',
      'target': 'spinning'}

# compound transition
t1 = {'trigger':'flip',
      'source':'spinning',
      'target':'heads'}
#      'function': coin_flip.flip_compound_transition}

t2 = {'trigger':'t',
      'source':'heads',
      'target':'spinning'}

t3 = {'trigger':'t',
      'source':'tails',
      'target':'spinning'}

# Change 3: We declare dicts for the states
spinning = {'name': 'spinning',
            'entry': 'on_spinning'}

heads = {'name': 'heads',
        'entry': 'on_heads;start_timer'}

tails = {'name': 'tails',
        'entry': 'on_tails;start_timer'}


# Change 4: We pass the set of states to the state machine
machine = Machine(name='coin_flip', transitions=[t0, t1, t2, t3], obj=coin_flip, states=[spinning, heads, tails])
coin_flip.stm = machine

driver = Driver()
driver.add_machine(machine)
driver.start()
