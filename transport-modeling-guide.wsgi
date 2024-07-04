import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/html/transport-modeling-guide")

from transport-modeling-guide import app as application
application.secret_key = 'ygQePmqS9hAugd6cGMQnLrIqcFkCWu3wzrfHnn7Bs0o'

