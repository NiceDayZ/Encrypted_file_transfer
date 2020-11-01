import socket
from Crypto.Cipher import AES

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

IP_address = str("127.0.0.1")
Port = int(3000)
server.connect((IP_address, Port))

K3 = b'Maria n-are mere'
K = b''
IV = b''
mode = ''


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


def thread_write():
    global server
    print("Starting writing to server")
    while True:
        try:
            message = str(input())
            server.send(message.encode("ascii"))
        except Exception as e:
            print(e)


def init():
    global mode
    confirmation = server.recv(2048)
    if confirmation.decode("ascii") == "T":
        temp = False
        while not temp:
            print("Select an encryption method. Type 1 for CBC or 2 for CFB")
            method_type = str(input())

            if method_type == "1":
                mode = "CBC"
                server.send(mode.encode("ascii"))
                temp = True
            elif method_type == "2":
                mode = "CFB"
                server.send(mode.encode("ascii"))
                temp = True
    elif confirmation.decode("ascii") == "F":
        print("Waiting the other client to chose his method of encryping")
        method = server.recv(2048)
        mode = method.decode('ascii')
        second_option = "CBC" if mode == "CFB" else "CFB"
        print("The other client choose " + second_option + " so your encryption method will be " + mode)
        server.send("MOD_RECEIVED".encode('ascii'))


def receive_key_and_iv():
    global K, IV

    temp_key = server.recv(16)
    K = decrypt_single_block(temp_key, K3)
    temp_iv = server.recv(16)
    IV = decrypt_single_block(temp_iv, K3)

    server.send(encrypt(b'K_IV_RECEIVED', mode, K, IV))


def start_sending_data():
    with open('from/2.pdf', mode='rb') as file:
        fileContent = file.read()
        encrypted_file = encrypt(fileContent, mode, K, IV)
        n = int(len(encrypted_file) / 16)
        server.send(encrypt(str(n).encode(), mode, K, IV))

        for i in range(n):
            data = encrypted_file[:16]
            server.send(data)
            encrypted_file = encrypted_file[16:]

        print("Done transferring data")
        confirmation = server.recv(16)
        if confirmation.decode('ascii') == 'DATA_RECEIVED':
            print("CLIENT B got the file safely")
        else:
            print("Something went wrong")



def start_receiving_data():
    message = server.recv(16)
    n = int(decrypt(message, mode, K, IV).decode('ascii'))

    encrypted_file = b''
    for i in range(n):
        encrypted_file += server.recv(16)

    decrypted_file = decrypt(encrypted_file, mode, K, IV)

    f = open('to/2.pdf', 'w+b')
    f.write(decrypted_file)
    f.close()

    server.send(b'DATA_RECEIVED')


def receive_and_execute_status():
    message = server.recv(128)
    if message.decode('ascii') == "RDY_TO_RECV":
        start_receiving_data()
    elif message.decode('ascii') == "RDY_TO_SEND":
        start_sending_data()


def start_reading_from_server():
    print("Starting reading from server")
    init()
    receive_key_and_iv()
    receive_and_execute_status()


start_reading_from_server()

server.close()

