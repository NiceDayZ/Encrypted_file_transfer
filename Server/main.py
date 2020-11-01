import socket
import threading
from Crypto.Cipher import AES
import os
import time

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

IP_address = str("127.0.0.1")
Port = int(3000)

server.bind((IP_address, Port))
server.listen(2)

connections = []
modes = ['', '']

K1 = os.urandom(16)
K2 = os.urandom(16)
K3 = b'Maria n-are mere'

IV1 = os.urandom(16)
IV2 = os.urandom(16)

ready_to_leave = False
close_server = False


def xor_for_bytes(input_bytes, key_input):
    return bytes(a ^ b for a, b in zip(input_bytes, key_input))


def pad(input_bytes):
    padding_size = (16 - len(input_bytes)) % 16
    if(padding_size == 0):
        padding_size = 16
    padding = (chr(padding_size) * padding_size).encode()
    return input_bytes+padding


def unpad(input_bytes):
    return input_bytes[:-ord(chr(input_bytes[-1]))]


def encrypt_single_block(input_bytes, key):
    return AES.new(key, AES.MODE_ECB).encrypt(input_bytes)


def decrypt_single_block(input_bytes, key):
    return AES.new(key, AES.MODE_ECB).decrypt(input_bytes)


def encryptCBC(input_bytes, key, iv):
    current_block = input_bytes[:16]
    current_iv = iv
    result = b''

    while len(input_bytes) > 0:
        cypher_text = encrypt_single_block(xor_for_bytes(current_iv, current_block), key)
        result += cypher_text

        input_bytes = input_bytes[16:]
        current_block = input_bytes[:16]
        current_iv = cypher_text

    return result


def decryptCBC(input_bytes, key, iv):
    current_block = input_bytes[:16]
    current_iv = iv
    result = b''

    while len(input_bytes) > 0:
        plain_text = xor_for_bytes(current_iv, decrypt_single_block(current_block, key))
        result += plain_text

        input_bytes = input_bytes[16:]
        current_iv = current_block
        current_block = input_bytes[:16]

    return result


def encryptCFB(input_bytes, key, iv):
    current_block = input_bytes[:16]
    current_iv = iv
    result = b''

    while len(input_bytes) > 0:
        cypher_text = xor_for_bytes(current_block, encrypt_single_block(current_iv, key))
        result += cypher_text

        input_bytes = input_bytes[16:]
        current_iv = cypher_text
        current_block = input_bytes[:16]

    return result



def decryptCFB(input_bytes, key, iv):
    current_block = input_bytes[:16]
    current_iv = iv
    result = b''

    while len(input_bytes) > 0:
        plain_text = xor_for_bytes(current_block, encrypt_single_block(current_iv, key))
        result += plain_text

        input_bytes = input_bytes[16:]
        current_iv = current_block
        current_block = input_bytes[:16]

    return result


def encrypt(input_bytes, method, key, iv):
    if method == "CBC":
        return encryptCBC(pad(input_bytes), key, iv)
    elif method == "CFB":
        return encryptCFB(pad(input_bytes), key, iv)


def decrypt(input_bytes, method, key, iv):
    if method == "CBC":
        return unpad(decryptCBC(input_bytes, key, iv))

    elif method == "CFB":
        return unpad(decryptCFB(input_bytes, key, iv))


def clientA_thread_read(conn, addr):
    global ready_to_leave
    print("Starting reading from clientA")
    conn.send("T".encode('ascii'))
    mode = conn.recv(2048)
    modes[0] = mode.decode('ascii')
    modes[1] = "CFB" if modes[0] == "CBC" else "CBC"

    conn.send(encrypt_single_block(K1, K3))
    conn.send(encrypt_single_block(IV1, K3))

    confirmation = decrypt(conn.recv(16), modes[0], K1, IV1)

    if confirmation != b'K_IV_RECEIVED':
        return None
    else:
        print("Node A confirmed it's KEY and IV")

    wait_for_a_change = True
    while wait_for_a_change:
        if (len(connections) == 2):
            wait_for_a_change = False

    conn.send("RDY_TO_SEND".encode('ascii'))

    message = conn.recv(16)
    n = int(decrypt(message, modes[0], K1, IV1).decode('ascii'))
    print(n)

    encrypted_file = b''

    for i in range(n):
        encrypted_file += conn.recv(16)

    decrypted_file = decrypt(encrypted_file, modes[0], K1, IV1)
    second_hand_encrypted_file = encrypt(decrypted_file, modes[1], K2, IV2)
    connections[1].send(encrypt(str(n).encode(), modes[1], K2, IV2))

    for i in range(n):
        data = second_hand_encrypted_file[:16]
        connections[1].send(data)
        second_hand_encrypted_file = second_hand_encrypted_file[16:]

    confirmation = connections[1].recv(16)
    if confirmation.decode('ascii') == 'DATA_RECEIVED':
        conn.send(confirmation)
        ready_to_leave = True
    else:
        conn.send('ERROR'.encode())



def clientB_thread_read(conn, addr):
    global close_server
    print("Starting reading from clientB")
    conn.send("F".encode('ascii'))

    wait_for_a_choice = True
    while wait_for_a_choice:
        if(modes[1] != ''):
            wait_for_a_choice = False

    conn.send(modes[1].encode('ascii'))

    confirmation = conn.recv(16)
    if confirmation.decode('ascii') != "MOD_RECEIVED":
        return None
    else:
        print("Node B confirmed it's encryption mode")

    conn.send(encrypt_single_block(K2, K3))
    conn.send(encrypt_single_block(IV2, K3))

    confirmation = decrypt(conn.recv(16), modes[1], K2, IV2)

    if confirmation != b'K_IV_RECEIVED':
        return None
    else:
        print("Node B confirmed it's KEY and IV")

    conn.send("RDY_TO_RECV".encode('ascii'))

    while not ready_to_leave:
        time.sleep(0.1)
        close_server=True


while not close_server:
    if(len(connections) != 2):
        conn, addr = server.accept()
        print(addr[0] + " connected")

        if len(connections) < 2:
            connections.append(conn)
            if len(connections) == 1:
                x = threading.Thread(target=clientA_thread_read, args=(conn, addr))
                x.start()
            else:
                x = threading.Thread(target=clientB_thread_read, args=(conn, addr))
                x.start()
        else:
            conn.close()
