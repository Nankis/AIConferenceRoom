import socket
import threading
import socketserver
import json
import utils.globalvar as gl


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def get_command(self, command):
        self.command = command

    def handle(self):
        data = self.request.recv(1024)
        jdata = json.loads(data.decode('utf-8'))
        print("Receive data from '%r'" % (data))
        print("Receive jdata from '%r'" % (jdata))

        # rec_request = jdata[0]['request']
        rec_request = jdata[0]['door_id']
        request_stauts = jdata[0]['request']
        cur_thread = threading.current_thread()

        if request_stauts == "open":
            response = [{
                'status': 'open'
            }]
        else:
            response = [{
                'status': 'close'
            }]
        jresp = json.dumps(response)
        self.request.sendall(jresp.encode('utf-8'))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def perform_commend(command):
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "localhost", 20000

    socketserver.TCPServer.allow_reuse_address = True

    TCR = ThreadedTCPRequestHandler
    TCR.command = command

    server = ThreadedTCPServer((HOST, PORT), TCR)
    ip, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    print(" .... waiting for connection")

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


#
if __name__ == "__main__":
    # set_global_command("open")
    # command = gl.get_value("command")
    # command = "open"
    command = "close"
    perform_commend(command)
    # print(get_global_status())
# # Port 0 means to select an arbitrary unused port
# HOST, PORT = "localhost", 20000
#
# socketserver.TCPServer.allow_reuse_address = True
#
# TCR = ThreadedTCPRequestHandler
# TCR.command = "open"
#
# server = ThreadedTCPServer((HOST, PORT), TCR)
# ip, port = server.server_address
# server_thread = threading.Thread(target=server.serve_forever)
# server_thread.daemon = True
# server_thread.start()
# print("Server loop running in thread:", server_thread.name)
# print(" .... waiting for connection")
#
# # Activate the server; this will keep running until you
# # interrupt the program with Ctrl-C
# server.serve_forever()


# door_response_msg = {
#     'state': 'open',  # 如果需要打开就返回open, 关闭返回close
# }
