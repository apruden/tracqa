import os
import trac.web.main

os.environ['TRAC_ENV'] = 'e:\\Workspace\\test\\'
application = trac.web.main.dispatch_request

from flup.server.fcgi import WSGIServer
server = WSGIServer(application, bindAddress=("127.0.0.1", 9000), )
server.run()

