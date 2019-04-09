# Logging

To debug your state machine, you can adjust the log level to see individual transitions. 
There are the following log levels:

* **DEBUG:** Most fine-grained logging, printing everything
* **INFO:**  Only the most important informational log items
* **WARN:**  Show only warnings and errors.
* **ERROR:** Show only error messages.

To change the log level for STMPY state machine:

```python
import logging
```

```python
debug_level = logging.DEBUG
logger = logging.getLogger('stmpy')
logger.setLevel(debug_level)
ch = logging.StreamHandler()
ch.setLevel(debug_level)
formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
```
