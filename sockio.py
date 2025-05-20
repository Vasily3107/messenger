from socket import socket
from jsonpickle import encode as jp_encode, decode as jp_decode


__ITERATION_END_SIGNAL = b'::looprecv_end_iteration::'
__ITERATION_END_LEN = len(__ITERATION_END_SIGNAL)


def send(conn:socket, data:dict) -> None:
    data = jp_encode(data).encode()
    conn.sendall(data + __ITERATION_END_SIGNAL)


def recv(conn:socket) -> dict:
    data = bytearray()

    while True:
        packet = conn.recv(8192)
        if packet.endswith(__ITERATION_END_SIGNAL):
            data.extend(packet[:-__ITERATION_END_LEN])
            break
        data.extend(packet)

    return jp_decode(bytes(data))