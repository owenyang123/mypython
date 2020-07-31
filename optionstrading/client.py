import socket
import time
PORT=6688
HEADER=64
FORMAT='utf-8'
DICMSG="done"
SERVER='10.85.209.89'
ADDR=(SERVER,PORT)
client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect(ADDR)
msg = raw_input("What's the symbol of your stock: ")
def send(msg):
    message=msg.encode(FORMAT)
    msg_length=len(message)
    send_length=str(msg_length).encode(FORMAT)
    send_length+=b' '*(HEADER-len(send_length))
    client.send(send_length)
    client.send(message)
    print client.recv(2048)

send(msg)
time.sleep(2)
send(DICMSG)