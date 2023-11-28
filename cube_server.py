# python 3.6
import json
from socket import *
import kociemba

# 1. 创建udp套接字

udp_socket = socket(AF_INET, SOCK_DGRAM)
udp_socket.bind(("0.0.0.0", 9000))


def run():
    print("服务器运行中.......")
    while True:
        try:
            recv_raw = udp_socket.recvfrom(9000)
            recv_data = json.loads(recv_raw[0].decode())
            dest_addr = recv_raw[1]
            ret = kociemba.solve(recv_data)
            print(ret)
        except Exception as e:
            print(e)
            ret = False
        finally:
            buffer = json.dumps(ret).encode()
            udp_socket.sendto(buffer, dest_addr)


if __name__ == '__main__':
    run()
