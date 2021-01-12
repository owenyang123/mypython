<<<<<<< HEAD
import socket
import threading

Port=6688
=======
import socket,threading
import stockplay as sp

PORT=6688
SERVER=socket.gethostbyname(socket.gethostname())

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

ADDR=('10.85.209.89',PORT)
print ADDR
server.bind(ADDR)

HEADER=64
FORMAT='utf-8'

DICMSG="done"

def handle_clinet(conn,addr):
    print addr[0]+" is coming with port "+str(addr[1])
    connected=True
    while connected:
        msg_len=conn.recv(HEADER).decode(FORMAT)

        if msg_len:
            msg_len=int(msg_len)
            msg=conn.recv(msg_len).decode(FORMAT)
            print(msg)
            if msg==DICMSG:connected=False
            else:
                temp1=sp.caifuziyou([msg][0])
                temp= " ".join([str(i) for i in temp1])
                print "sent "+temp
                conn.send(temp.encode(FORMAT))
    conn.close()


def start():
    server.listen(5)
    while True:
        conn,addr=server.accept()
        thread=threading.Thread(target=handle_clinet,args=(conn,addr))
        thread.start()

print "ready"

start()
>>>>>>> bd0b7fa129262ff7e84455e5bc7ada8bd15f877a
