"""
    Script to create a server which calls the model.step from
    an MAS implementation
"""


# Install pyngrok to propagate the http server
# pip install pyngrok

# Load the required packages
from pyngrok        import ngrok
from http.server    import BaseHTTPRequestHandler, HTTPServer

import json
import logging
import os

# Import MAS module
from agentes import Interseccion
from agentes import all_agents_crossed

model = Interseccion(200, 50)

maxIter = 1000

def features(data):
    dataJson = {}
    dataJson["Semaforos"] = data[0]
    dataJson["Peatones"] = data[1]
    dataJson["Carros"] = data[2]

    return json.dumps(dataJson)

class Server(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n",
                     str(self.path), str(self.headers))
        self._set_response()
        model.step()
        data = model.status_agents()
        # obtener los datos del modelo...
        #resp = "{\"data\":" + features(data) + "}"
        resp = features(data)
        self.wfile.write(resp.encode('utf-8'))

    def do_POST(self):
        pass

def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    public_url = ngrok.connect(port).public_url
    logging.info(f"ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:{port}\"")

    logging.info("Starting httpd...\n") # HTTPD is HTTP Daemon!
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:   # CTRL + C stops the server
        pass

    httpd.server_close()
    logging.info("Stopping httpd...\n")


if __name__ == "__main__":
    # server
    run(HTTPServer, Server)
    
