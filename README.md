# Documentatie Encrypted_Secured_Transfer

### Prereq: Python 3.0+
### Pentru a putea rula atat serverul cat si clientul este necesara instalarea librariei pycryptodome

`pip install pycryptodome`

#### Pentru a rula serverul:

```bash
	python3 ./Server/main.py
```

#### Pentru a rula clientul:

```bash
	python3 ./Client/main.py
```

## Scurta descriere a modului de operare a serverului (KM)

#### Ne vom referi in continuare la server sub numele de KM (Key Manager) si la 2 clienti conectati la KM consecutiv ca A, respectiv B

#### Este necesara pornirea lui KM la inceput. KM va genera in aceasta ordine 4 vectori de bytes care reprezinta

 - K1 este cheia care va fi atribuita primului client care se va conecta
 - K2 este cheia care va fi atribuita celui de-al doilea client
 - IV1 este vectorul de initializare a primului client
 - IV2 este vectorul de initializarre a celui de-al doilea client

Link to code: [Keys init](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Server/main.py#L19)
 
 #### K3 este cheia publica si este initializata cu valoarea `b'Maria n-are mere'` de lungime 128 bits. Serverul apoi asteapta connectarea clientilor. KM nu accepta decat maxim 2 clienti conectati simultan. Daca primul client se conecteaza, acesta este interogat asupra modului de operare dorit (CBC sau CFB).

Link to code: [Server waiting for clients](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Server/main.py#L221)
 
#### La nivel de client acest lucru se realizeaza introducand de la tastatura 1 pentru CBC sau 2 pentru CFB. Odata ales modul de operare de clientul A, KM asteapta connectarea celui de-al doilea client. Cand acesta se conecteaza serverul ii trimite clientului B modul de operare (diferit fata de cel ales de clientu A) apoi asteapta confirmarea de la clientul B ca acesta a primit modul de operare corect. 

#### Dupa confirmarea modurilor de operare KM cripteaza cheile K1 si K2 si vectorii de initializare in modurile alese de clienti si le transmite acestora, apoi asteapta confirmarea de primire de la cei 2 (criptate in modurile alese cu cheile specifice).

#### Dupa ce este primita confirmarea, serverul trimite celor 2 clienti confirmarea ca pot incepe sa isi desfasoare rolul de transmitator, respectiv receptor.

#### KM primeste de la A, criptat prin modul ales de acesta si cu cheia K1 un numar n si apoi n pachete de cate 16 octeti. KM decripteaza pachetele cu K1 si apoi le encripteaza cu K2 in modul ales de client B, si le transmite in aceiasi maniera catre B. Dupa ce toate pachetele sunt transmise lui B, asteapta confirmarea acestuia, pe care o trimite catre A, apoi inchide procesul si comunicarea.

## Scurta descriere a modului de operare a clientului (A respectiv B)

#### Ambii clienti initializeaza K3 cu valoarea `b'Maria n-are mere'`

#### O sa consideram 2 cazuri:

#### A: clientul s-a conectat primul la KM

#### B: clientul s-a conectat al doilea la KM

### Clientii se conecteaza:

#### A: Este promptat sa aleaga modul de operare dorit

#### B: Asteapta pana cand A alege modul, si ii este trimis modul de operare in care acesta va cripta, apoi trimite confirmare la server

Link to code: [Client Init](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L130)

### Clientii primesc cheile si IV:

#### A,B: Asteapta de la KM cheile si IV, criptate cu K3. Acestia decripteaza cheile si IV si trimit un mesaj de confirmare criptat in modurile specifice fiecaruia cu cheile si IV-urile primite.

Link to code: [Receive Key and IV](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L156)

### Inceperea transferului:

#### Clientii asteapta confirmarea de la server ca isi pot incepe comunicarea.

#### A preia continutul in bytes al unui fisier si il encripteaza in modul specific cu K1 si IV1, apoi trimite la server un numar intreg `n` ce reprezinta numarul de blocuri pe care urmeaza sa le transmita, apoi trimite cele n blocuri.

#### B primeste de la server un numar intreg `n` ce reprezinta numarul de blocuri pe care urmeaza sa le primeasca, apoi primeste n blocuri pe care le decripteaza cu K2 si IV2, apoi pune vectorul de bytes intr-un fisier.

Link to code: [Receive and Execute Status](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L205)

### Incheierea conexiunii:

#### B trimite catre KM confirmarea primirii integre a pachetelor.

#### A primeste confirmarea de la KM ca B a primit pachetele.

#### A, B isi termina executia


## Demonstratie functionare:
	
### La o rulare cu succes a intregului flow al programelor se poate observa ca in folderul `Client/to` va aparea fisierul 2.pdf, care a fost preluat de clientul A din folderul `Client/from` si salvat de clientul B. Dupa executie se observa ca fisierul poate fi deschis si prelucrat in mod obisnuit

## Functii importante:

#### `encrypt(input_bytes, method, key, iv)` - paddeaza si encripteaza un vector de bytes in functie de modul de operare ales (CBC sau CFB). Returneaza un vector de bytes ce reprezinta inputul cryptat cu cheia `key` si vectorul de initializare `iv`.

Link to code: [encrypt](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L104)

___

#### `decrypt(input_bytes, method, key, iv)` - decripteaza si scoate paddingul unui input de bytes in functie de modul de operare ales. Returneaza un vector de bytes ce reprezinta inputul cryptat cu cheia `key` si vectorul de initializare `iv`.

Link to code: [decrypt](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L111)

___

#### `encrypt(CBC)/(CFB)(input_bytes, key, iv)` - Versiunile specifice ale functiei `encrypt` de mai sus, fara padding. 

Link to code: [CBC](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L40) [CFB](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L72)

___

#### `decrypt(CBC)/(CFB)(input_bytes, key, iv)` - Versiunile specifice ale functiei `decrypt` de mai sus, fara depadding.

Link to code: [CBC](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L56) [CFB](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L88)

___

#### `(decrypt)/(encrypt)_single_block(input_bytes, key)` - Decripteaza/Cripteaza un singur bloc in mod AES_ECB. Utilizat de functiile de mai sus

Link to code: [encrypt](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L32) [decrypt](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L36)

___

#### `(un)pad(input_bytes)` - Adauga/Scoate paddingul unui bloc in mod PKCS#7.

Link to code: [pad](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L20) [unpad](https://github.com/NiceDayZ/Encrypted_file_transfer/blob/3167d02ee15cc5c53b9d5bf05e2442ffe189323c/Client/main.py#L28)


