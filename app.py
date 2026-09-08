import os
import logging
from app import utility
from app import logger
from app import create_app

app = create_app()


def Main():

  logger.SetupLogger(app.config['LOGFILE'])

  if (utility.LOG_LEVEL == 20):
    # this surpresses all the flask messages to sdout
    logging.getLogger('werkzeug').disabled = True
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'

  # write pid and port data to disk
  # utility.file_program_manager(app.config['PIDFILE'], 'create', '%s' % utility.PID)
  # utility.file_program_manager(app.config['RESTFUL_OPS_PORT_FILE'], 'create', '%s' % app.config['APP_PORT'])
  # utility.file_program_manager(app.config['RESTFUL_OPS_HOST_FILE'], 'create', '%s' % app.config['APP_HOST'])

  # for item in app.config.iteritems():
  #   print item

  # if (utility.LOG_LEVEL == 20):
  #   app.run(debug=False, threaded=True, host=app.config['APP_HOST'], port=int(app.config['APP_PORT']))
  # else:
  app.run(debug=True, threaded=True, host=app.config['APP_HOST'], port=int(app.config['APP_PORT']))


if __name__ == '__main__':
  Main()
