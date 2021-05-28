import socket
from _thread import *

server = "192.168.1.12"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Types of connection / TCP socket (socket is IP + Port number)

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2) #Number of people allowed on server
print("Waiting for a connection, Server Started")


def threaded_client(conn): #Threaded basically means multiple things can be running at the same time
    conn.send(str.encode("Connected"))
    reply = ""
    while True:
        try:
            data = conn.recv(2048) #Amount of bits allowed to receive
            reply = data.decode("utf-8") #Decode so it is human readable

            if not data:
                print("Disconnected")
                break
            else:
                print("Received: ", reply)
                print("Sending :", reply)

            conn.sendall(str.encode(reply)) #Encode again so it is secure
        except:
            break
    
    print("Lost connection")
    conn.close()

while True:
    conn, addr = s.accept()
    print("Connected to: ", addr)

    start_new_thread(threaded_client, (conn,))
    