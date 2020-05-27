from socket import *
import threading
import hashlib
import sys
import time
import os
import random

#The finger table only contains users that aren't the client or successor

Offset = random.randint(2**25, 2**50)
Port = 0
User = []
Successor = []
SuccessorsSuccessor = []
FingerTable = []

Address = ""

def recvKey(conn):
    return int.from_bytes(recvAll(conn, 20), byteorder="big")

#IPs are stored in the stringformat so they are read yo be plugged in to the .connect() function
#This strips the all the periods so an ip can be sent as a 4 byte int
def IntefyIP(rev_ip):
    new_ip = rev_ip[:2]
    new_ip = new_ip + rev_ip[3:5]
    new_ip = new_ip + rev_ip[6:8]
    new_ip = new_ip + rev_ip[9:]
    new_ip = int(new_ip)
    return new_ip

#Does the opposite of the IntefyIP() it take inscoming int IPs and puts periods in
def StringifyIP(ip):
    ip = str(ip)
    sending_ip = str(ip[:2])
    sending_ip = sending_ip + "."
    sending_ip = sending_ip + ip[2:4]
    sending_ip = sending_ip + "."
    sending_ip = sending_ip + ip[4:6]
    sending_ip = sending_ip + "."
    sending_ip = sending_ip + ip[6:]
    return sending_ip

#The contents of each finger list is returned in order of index, ip, and port
def TableBreaker(finger):
    return str(finger[0]), str(finger[1]), str(finger[2])

def getHashIndex(addr):
    b_addrStr = (addr).encode()
    b_addrStr = hashlib.sha1(b_addrStr).digest()
    return_addr = int.from_bytes(b_addrStr, byteorder="big")
    return return_addr

def recvAll(conn, msgLength):
    msg = b''
    while len(msg) < msgLength:
        retVal = conn.recv(msgLength - len(msg))
        msg += retVal
        if len(retVal) == 0:
            break
    return msg

#Converts bytes into a string and strips the single quotes and "b" in the start
def ByteToString(Bytes):
    Bytes = str(Bytes)
    Bytes = Bytes[2:len(Bytes)-1]
    return Bytes

#Put in a new table as the finger table. Only used when replacing the whole table
def InsertToTable(addr):
    global FingerTable
    FingerTable = []
    for i in range(0, len(addr)):
        FingerTable.append(addr[i])

#Returns the finger table along with the successor
def GiveTable():
    global FingerTable
    global Successor
    return_table = []
    return_table = FingerTable
    return_table.append(Successor)
    return return_table

#Runs through all the scenarios where the user can own a key space.
#Returns true if owner, false if not the owner
def IOwn(key_index):
    global User
    global Successor
    if not Successor:
        return False
    my_index, my_ip, my_port = TableBreaker(User)
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    suc_index = int(suc_index)
    my_index = int(my_index)
    key_index = int(key_index)
    #If the user's index matches their successor's index. Should only happen in a 1 man DHT
    if my_index == suc_index:
        return True
    #If the key is between User and Successor.
    #Can only work if the successor numerically greater than the user
    if key_index > my_index and key_index < suc_index:
        return True
    #If the Successor is numerically behind the User and the key is less than the user
    #Should only happen if the User has the largest index and the successor has the smallest index
    if suc_index < my_index and key_index < suc_index:
        return True
    #If the Successor is also numerically smaller but the key is still larger than the User's
    if suc_index < my_index and key_index > my_index:
        return True
    else:
        return False

def RequestSuccessor():
    global Successor
    global SuccessorsSuccessor
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    suc_index2, suc_ip2, suc_port2 = TableBreaker(SuccessorsSuccessor)
    if str(suc_index) == str(suc_index2):
        return Successor
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((suc_ip, int(suc_port)))
    conn.send("ABD".encode())
    next_owner = recvAll(conn, 4)
    next_port = recvAll(conn, 2)
    next_owner = int.from_bytes(next_owner, byteorder="big")
    next_owner = StringifyIP(next_owner)
    next_port = int.from_bytes(next_port, byteorder="big")
    hash = str(next_owner) + ":" + str(next_port)
    SuccessorsS = [getHashIndex(hash), next_owner, next_port]
    return SuccessorsS
    
def Pulse():
    global User
    global Successor
    global SuccessorsSuccessor
    my_index, my_ip, my_port = TableBreaker(User)
    if len(Successor) > 0:
        suc_index, suc_ip, suc_port = TableBreaker(Successor)
        #If the Successor and User are the same person, which only happens in a 1 man DHT
        #This type of checking is done often to assure wasteful actions or weird errors don't occur so it simply return
        if (suc_index == my_index):
            return
        try:
            conn = socket(AF_INET, SOCK_STREAM)
            conn.connect((suc_ip, int(suc_port)))
            conn.send("PUL".encode())
            conn.recv(1)
        except:
            Successor = SuccessorsSuccessor
            SuccessorsSuccessor = RequestSuccessor()
    if SuccessorsSuccessor != None and len(SuccessorsSuccessor) > 0:
        suc_index2, suc_ip2, suc_port2 = TableBreaker(SuccessorsSuccessor)
        #If the Successor and User are the same person, which only happens in a 1 man DHT
        #This type of checking is done often to assure wasteful actions or weird errors don't occur so it simply return
        if (suc_index2 == my_index):
            return
        try:
            conn = socket(AF_INET, SOCK_STREAM)
            conn.connect((suc_ip2, int(suc_port2)))
            conn.send("PUL".encode())
            conn.recv(1)
        except:
            SuccessorsSuccessor = RequestSuccessor()
    NewTable = []
    global FingerTable
    i = 0
    while i > len(FingerTable):
        index, ip, port = TableBreaker(FingerTable[i])
        if index != my_index:
            try:
                conn = socket(AF_INET, SOCK_STREAM)
                conn.connect((ip, int(port)))
                conn.send("PUL".encode())
                reply = connect.recv(1)
                reply = ByteToString(reply)
                NewTable.append(FingerTable[i])
            except:
                for i in range(0, len(NewTable)):
                    NewTable.pop(FingerTable[i])
    FingerTable = NewTable

#The Owns functionality that is used by almost all functions
def findOwner(key):
    global SuccessorsSuccessor
    global Successor
    if len(Successor) > 0:
        Pulse()
        SuccessorsSuccessor = RequestSuccessor()
    global FingerTable
    Where = []
    Distances = []
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    #Check if the User owns that keyspace.
    #Every function will appropriately respond if the User's IP and Port is returned from this check
    if IOwn(key) == True:
        return socket(AF_INET, SOCK_STREAM), myIP, myPort
    #Check the closest peer's index that is still smaller than the wanted keyspace
    for i in range(0, len(FingerTable)):
        index, ip, port = TableBreaker(FingerTable[i])
        index = int(index)
        if key > int(index) and int(index) != int(myIndex):
            Distances.append(key-index)
            Where.append(i)
    if len(Distances) > 0:
        smallest = min(Distances)
        index_of = Distances.index(smallest)
        Where_is_it = Where[index_of]
        index, ip, port = TableBreaker(FingerTable[Where_is_it])
        if index == myIndex:
            return socket(AF_INET, SOCK_STREAM), myIP, myPort
    else:
        #If no one suitable can be found just refer to Successor
        index, ip, port = TableBreaker(Successor)
    talking_with = ip
    next_owner =""
    key = key.to_bytes(20, byteorder='big')
    #Connect with someone previously found and ask them if they own that keyspace
    #Continue to connect to people until someone reponds with their own information
    while talking_with != next_owner:
        conn = socket(AF_INET, SOCK_STREAM)
        conn.connect((talking_with, int(port)))
        conn.send(("OWN").encode())
        conn.send(key)
        msg = b''
        next_owner = recvAll(conn, 4)
        next_port = recvAll(conn, 2)
        next_owner = int.from_bytes(next_owner, byteorder="big")
        next_owner = StringifyIP(next_owner)
        next_port = int.from_bytes(next_port, byteorder="big")
        if next_owner == talking_with and next_port == port:
            return conn, talking_with, port
        if next_owner == myIP and next_port == myPort:
            return socket(AF_INET, SOCK_STREAM), myIP, myPort
        else:
            talking_with = next_owner
            next_owner = ""
            port = next_port
            next_port = ""

#Go through and ask who currently owns every 5th minus Offset and make that list the new FingerTable
def UpdateTable():
    new_list = []
    temp = []
    global Offset
    for i in range(1, 6):
        #When doing math on large numbers python puts it in scientific notation.
        #So I set everythin to int to make sure no scietific notation is every used
        multiplying = 2**160
        multiplying = int(multiplying)
        multiplying = multiplying / 5
        multiplying = multiplying * i
        multiplying = int(multiplying)
        multiplying = multiplying - Offset
        key = multiplying.to_bytes(20, byteorder='big')
        owner, ip, port = findOwner(int(multiplying))
        hash = str(ip) + ":" + str(port)
        new_list.append([getHashIndex(hash), ip, port])
    InsertToTable(new_list)

#Most function from here are ones innitiated by the user or handle requests from  peers
#Any functions that handle incoming peer requests have "Handle" in front of them
def InsertFile(sending_file):
    hashed_index = getHashIndex(sending_file)
    Send_File = open("repository/" + str(sending_file), "rb").read()
    Owner, ip, port = findOwner(hashed_index)
    Owner = socket(AF_INET, SOCK_STREAM)
    Owner.connect((ip, int(port)))
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    #If User owns this keyspace simply move the file with its hashed name into their "storing" folder
    if IOwn(hashed_index) == True:
        Putting_File = open("storing/" + str(hashed_index), "wb+")
        Putting_File.write(Send_File)
        Putting_File.close()
        return "This keyspace is owned by you. Congrats with moving that file from one folder to another"
    Feedback = ""
    while Feedback != "T":
        Owner.send("INS".encode())
        hashed_index = hashed_index.to_bytes(20, byteorder='big')
        Owner.send(hashed_index)
        Feedback = Owner.recv(1)
        Feedback = ByteToString(Feedback)
        if Feedback == "N":
            Owner, ip, port = findOwner(hashed_index)
            Owner = socket(AF_INET, SOCK_STREAM)
            Owner.connect((ip, int(port)))
        else:
            Length = len(Send_File)
            Length = Length.to_bytes(8, byteorder='big')
            Owner.send(Length)
            Owner.send(Send_File)
            Feedback = Owner.recv(1)
            Feedback = ByteToString(Feedback)
            if Feedback == "F":
                return "Failed. Likely due to not enough space on the client's machine."
            if Feedback == "T":
                return "Success"

def HandleInfo(connection):
    global User
    global Successor
    global SuccessorsSuccessor
    global FingerTable
    my_index, my_ip, my_port = TableBreaker(User)
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    suc_index2, suc_ip2, suc_port2 = TableBreaker(SuccessorsSuccessor)
    Owner, pred_ip, pred_port = findOwner(int(my_index)-1)
    pred_hash = getHashIndex(str(pred_ip) + ":" + str(pred_port))
    Predecessor = "pred: " + str(pred_hash) +  "(" + str(pred_ip) + ":" + str(pred_port) + ")"
    Predecessor = Predecessor.encode()
    Length = len(Predecessor)
    connection.send(Length)
    connection.send(Predecessor)
    Succ = "succ1: " + str(suc_index) +  "(" + str(suc_ip) + ":" + str(suc_port) + ")"
    Succ.encode()
    Succ = Succ.encode()
    Length = len(Succ)
    connection.send(Length)
    connection.send(Succ)
    Succ2 = "succ2: " + str(suc_index2) +  "(" + str(suc_ip2) + ":" + str(suc_port2) + ")"
    Succ2.encode()
    for i in range(0, len(FingerTable)):
        index, ip, port = TableBreaker(FingerTable[i])
        Finger = "[" + str(i) + "]" + str(index) +  "(" + str(ip) + ":" + str(port) + ")"
        Finger = Finger.encode()
        Length = len(Finger)
        connection.send(Length)
        connection.send(Finger)

#Send a remove request or remove from user's own directory if its within their own keyspace ownership
def Remove(deleting_file):
    hashed_index = getHashIndex(deleting_file)
    Owner, ip, port = findOwner(hashed_index)
    Owner = socket(AF_INET, SOCK_STREAM)
    Owner.connect((ip, int(port)))
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    if IOwn(hashed_index) == True:
        os.remove("storing/" + str(hashed_index))
        return("You owned the file. It has been removed from your storing folder")
    Feedback = ""
    while Feedback != "T":
        Owner.send("REM".encode())
        hashed_index = hashed_index.to_bytes(20, byteorder='big')
        Owner.send(hashed_index)
        Feedback = Owner.recv(1)
        Feedback = ByteToString(Feedback)
        if Feedback == "N":
            Owner, ip, port = findOwner(index)
            Owner = socket(AF_INET, SOCK_STREAM)
            Owner.connect((ip, int(port)))
        if Feedback == "F":
            return "Failed"
        if Feedback == "T":
            return "Success"

#Download and write the specified file
def Get(get_file):
    hashed_index = getHashIndex(get_file)
    Owner, ip, port = findOwner(hashed_index)
    Owner = socket(AF_INET, SOCK_STREAM)
    Owner.connect((ip, int(port)))
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    if IOwn(hashed_index) == True:
        try:
            Writting_File = open("storing/" + str(hashed_index), "r").read()
        except:
            return "You own the keyspace and the file doesn't exist"
        Putting_File = open("repository/" + str(hashed_index), "w+")
        Putting_File.write(Writting_File)
        Putting_File.close()
        return "You owned the file space. Congrats you moved it from the storing folder to the repository folder"
    Feedback = ""
    while Feedback != "T":
        Owner.send("GET".encode())
        hashed_index = hashed_index.to_bytes(20, byteorder='big')
        Owner.send(hashed_index)
        Feedback = Owner.recv(1)
        Feedback = ByteToString(Feedback)
        if Feedback == "N":
            Owner, ip, port = findOwner(hashed_index)
            Owner = socket(AF_INET, SOCK_STREAM)
            Owner.connect((ip, int(port)))
        if Feedback == "F":
            return "The file doesn't exist"
        if Feedback == "T":
            valSize = recvAll(Owner, 8)
            valSize = int.from_bytes(valSize, byteorder='big')
            val = recvAll(Owner, int(valSize))
            Writer = open("repository/" + get_file, "wb+")
            Writer.write(val)
            Writer.close()
            return "You got the file"

#Request a file existance check
def Exists(exist_file):
    hashed_index = getHashIndex(exist_file)
    Feedback = ""
    Owner, ip, port = findOwner(hashed_index)
    Owner = socket(AF_INET, SOCK_STREAM)
    Owner.connect((ip, int(port)))
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    if IOwn(hashed_index) == True:
        Repository_List = os.listdir("storing")
        if str(hashed_index) in Repository_List:
            return "You own the keyspace to the file and it in fact exists"
        else:
            return "You own the keyspace. Though the file doesn't exist"
    while Feedback != "T":
        Owner.send("EXI".encode())
        hashed_index = hashed_index.to_bytes(20, byteorder='big')
        Owner.send(hashed_index)
        Feedback = Owner.recv(1)
        Feedback = ByteToString(Feedback)
        if Feedback == "N":
            Owner, ip, port = findOwner(hashed_index)
            Owner = socket(AF_INET, SOCK_STREAM)
            Owner.connect((ip, int(port)))
        if Feedback == "F":
            return "The file doesn't exist"
        if Feedback == "T":
            return "The file does exist"

#Receive a file to insert. Attemp to add it if User owns the keyspace.
#If for some reason it crashes when trying to add it send "F"
def HandleInsert(connection):
    key = recvAll(connection, 20)
    key = int.from_bytes(key, byteorder="big")
    if IOwn(key) == True:
        try:
            connection.send("T".encode())
            valSize = recvAll(connection, 8)
            valSize = int.from_bytes(valSize, byteorder="big")
            val = recvAll(connection, valSize)
            writing = open("storing/" + str(key), "wb+")
            writing.write(val)
            writing.close()
            connection.send("T".encode())
        except:
            connection.send("F".encode())
    else:
        connection.send("N".encode())

#Remove a file if user owns it
def HandleRemove(connection):
    key = recvAll(connection, 20)
    key = int.from_bytes(key, byteorder="big")
    global User
    index, ip, port = TableBreaker(User)
    if IOwn(key):
        Repository_List = os.listdir("storing")
        for i in range(0, len(Repository_List)):
            List_Item = str(Repository_List[i])
            if List_Item == str(key):
                os.remove("storing/" + List_Item)
                connection.send("T".encode())
                return
        connection.send("F".encode())
        return
    else:
        connection.send("N".encode())
        return

#Send any requested file if User owns it
def HandleGet(connection):
    key = recvAll(connection, 20)
    key = int.from_bytes(key, byteorder="big")
    global User
    OwnIndex, OwnIP, Ownport = TableBreaker(User)
    Owner, ip, port = findOwner(key)
    if IOwn(key) == True:
        #print("WE OWN THE FILESPACE")
        Repository_List = os.listdir("storing")
        for i in range(0, len(Repository_List)):
            List_Item = str(Repository_List[i])
            if List_Item == str(key):
                connection.send("T".encode())
                Send_File = open("storing/" + List_Item, "rb").read()
                Length = len(Send_File)
                Length =  Length.to_bytes(8, byteorder='big')
                connection.send(Length)
                connection.send(Send_File)
                return
        connection.send("F".encode())
        returnF
    else:
        connection.send("N".encode())
        return

#Tell peer if the file exists
def HandleExist(connection):
    key = recvAll(connection, 20)
    key = int.from_bytes(key, byteorder="big")
    global User
    OwnIndex, OwnIP, Ownport = TableBreaker(User)
    Owner, ip, port = findOwner(key)
    if ip == OwnIP:
        Repository_List = os.listdir("storing")
        for i in range(0, len(Repository_List)):
            List_Item = str(Repository_List[i])
            if List_Item == str(key):
                connection.send("T".encode())
                return 
        connection.send("F".encode())
        return
    else:
        connection.send("N".encode())
        return

#Reply to an owns check
def HandleOwn(connection):
    key = recvAll(connection, 20)
    key = int.from_bytes(key, byteorder="big")
    if IOwn(key) == False:
        Table = GiveTable()
        Distances = []
        Where = []
        #Similar to the findOwner() function the closest peer is looked for if the User doesn't own the keyspace
        for i in range(0, len(Table)):
            index, ip, port = TableBreaker(Table[i])
            if key > int(index):
                Distances.append(key-int(index))
                Where.append(i)
        if len(Distances) > 0:
            smallest = min(Distances)
            index_of = Distances.index(smallest)
            Where_is_it = Where[index_of]
            index, ip, port = TableBreaker(Table[Where_is_it])
            ip = IntefyIP(ip)
        else:
            index, ip, port = TableBreaker(Successor)
            ip = IntefyIP(ip)
        ip = ip.to_bytes(4, byteorder='big')
        connection.send(ip)
        port = int(port)
        port = port.to_bytes(2, byteorder='big')
        connection.send(port)
    else:
        global User
        myIndex, myIP, myPort = TableBreaker(User)
        myIP = IntefyIP(myIP)
        myIP = myIP.to_bytes(4, byteorder='big')
        myPort = int(myPort)
        myPort = myPort.to_bytes(2, byteorder='big')
        connection.send(myIP)
        connection.send(myPort)
        return 

#Handle an incoming connection. If the User owns the keyspace then simply send them any files they now own and make tat peer the new successor
def HandleConnection(connection):
    incoming_ip = recvAll(connection, 4)
    incoming_port = recvAll(connection, 2)
    incoming_ip = int.from_bytes(incoming_ip, byteorder='big')
    incoming_ip = StringifyIP(incoming_ip)
    incoming_port = int.from_bytes(incoming_port, byteorder='big')
    hash = incoming_ip + ":" + str(incoming_port)
    connection_index = getHashIndex(hash)
    global User
    myIndex, myIP, myPort = TableBreaker(User)
    global SuccessorsSuccessor
    global Successor
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    if Successor != SuccessorsSuccessor:
        suc_index2, suc_ip2, suc_port2 = TableBreaker(SuccessorsSuccessor)
    #This is to prevent the 2nd person who joing from thinking their successor is also their successor's successor
    #When the second person joins they will be told they are their successor's successor
    else:
        suc_index2 = connection_index
        suc_ip2 = incoming_ip
        suc_port2 = incoming_port
    if IOwn(connection_index) == True:
        connection.send("T".encode())
        suc_ip = IntefyIP(suc_ip)
        suc_ip = suc_ip.to_bytes(4, byteorder="big")
        connection.send(suc_ip)
        suc_port = int(suc_port)
        suc_port = suc_port.to_bytes(2, byteorder="big")
        connection.send(suc_port)
        suc_ip2 = IntefyIP(suc_ip2)
        suc_ip2 = suc_ip2.to_bytes(4, byteorder="big")
        connection.send(suc_ip2)
        suc_port2 = int(suc_port2)
        suc_port2 = suc_port2.to_bytes(2, byteorder="big")
        connection.send(suc_port2)
        Repository_List = os.listdir("storing")
        Length = 0
        for i in range(0, len(Repository_List)):
            List_Item = str(Repository_List[i])
            if int(Repository_List[i]) > int(connection_index):
                Length = Length + 1
        Length = Length.to_bytes(8, byteorder='big')
        connection.send(Length)
        for i in range(0, len(Repository_List)):
            if int(Repository_List[i]) > int(connection_index):
                List_Item = str(Repository_List[i])
                File = open("storing/" + List_Item, "rb").read()
                List_Item = int(List_Item)
                List_Item = List_Item.to_bytes(20, byteorder='big')
                connection.send(List_Item)
                Length = len(File)
                Length = Length.to_bytes(8, byteorder='big')
                connection.send(Length)
                connection.send(File)
        SuccessorsSuccessor = Successor
        Successor = [connection_index, incoming_ip, incoming_port]
    else:
        connection.send("N".encode())

#Receive all the files and take control of their keyspace if the peer is User's Successor
def HandleDisconnect(connection):
    ip = recvAll(connection, 4)
    ip = int.from_bytes(ip, byteorder="big")
    ip = StringifyIP(ip)
    port = recvAll(connection, 2)
    port = int.from_bytes(port, byteorder="big")
    hashed = getHashIndex(str(ip) + ":" + str(port))
    global Successor
    global SuccessorsSuccessor
    suc_key, suc_ip, suc_port = TableBreaker(Successor)
    if str(suc_key) == str(hashed):
        connection.send("T".encode())
    else:
        connection.send("N".encode())
        return
    ip = recvAll(connection, 4)
    ip = int.from_bytes(ip, byteorder="big")
    ip = StringifyIP(ip)
    port = recvAll(connection, 2)
    port = int.from_bytes(port, byteorder="big")
    hashed = getHashIndex(str(ip) + ":" + str(port))
    Successor = [hashed, ip, port]
    ip2 = recvAll(connection, 4)
    ip2 = int.from_bytes(ip2, byteorder="big")
    ip2 = StringifyIP(ip2)
    port2 = recvAll(connection, 2)
    port2 = int.from_bytes(port2, byteorder="big")
    hashed2 = getHashIndex(str(ip2) + ":" + str(port2))
    SuccessorsSuccessor = [hashed2, ip2, port2]
    numItems = recvAll(connection, 8)
    numItems = int.from_bytes(numItems, byteorder="big")
    Items_Downloaded = 0
    while Items_Downloaded != numItems:
        key = recvAll(connection, 20)
        key = int.from_bytes(key, byteorder="big")
        valSize = recvAll(connection, 8)
        valSize = int.from_bytes(valSize, byteorder="big")
        val = recvAll(connection, valSize)
        f = open(("storing/"+str(key)), "wb+")
        f.write(val)
        f.close()
        Items_Downloaded = Items_Downloaded + 1
    connection.send("T".encode())
    UpdateTable()

#Disconnect and send all files to predecessor
def Disconnect():
    global User
    global Successor
    global SuccessorsSuccessor
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    suc_index2, suc_ip2, suc_port2 = TableBreaker(SuccessorsSuccessor)
    suc_ip = IntefyIP(suc_ip)
    suc_port = int(suc_port)
    suc_ip = suc_ip.to_bytes(4, byteorder='big')
    suc_port = suc_port.to_bytes(2, byteorder='big')
    suc_ip2 = IntefyIP(suc_ip2)
    suc_port2 = int(suc_port2)
    suc_ip2 = suc_ip2.to_bytes(4, byteorder='big')
    suc_port2 = suc_port2.to_bytes(2, byteorder='big')
    myIndex, myIP, myPort = TableBreaker(User)
    Owner, ip, port = findOwner(int(myIndex)-1)
    Owner = socket(AF_INET, SOCK_STREAM)
    if ip == myIP and myPort == port:
        return
    Owner.connect((ip, int(port)))
    Owner.send("DIS".encode())
    myIP = IntefyIP(myIP)
    myPort = int(myPort)
    myIP = myIP.to_bytes(4, byteorder='big')
    myPort = myPort.to_bytes(2, byteorder='big')
    Owner.send(myIP)
    Owner.send(myPort)
    Responce = ""
    while Responce != "T":
        Responce = Owner.recv(1)
        Responce = ByteToString(Responce)
        if Responce == "F":
            Owner, ip, port = findOwner(int(myIndex)-1)
            Owner = socket(AF_INET, SOCK_STREAM)
            Owner.connect((ip, int(port)))
            Owner.send("DIS".encode())
            Owner.send(myIP)
            Owner.send(myPort)
    Owner.send(suc_ip)
    Owner.send(suc_port)
    Owner.send(suc_ip2)
    Owner.send(suc_port2)
    Repository_List = os.listdir("storing")
    Length = 0
    for i in range(0, len(Repository_List)):
        List_Item = str(Repository_List[i])
        Length = Length + 1
    Length = Length.to_bytes(8, byteorder='big')
    Owner.send(Length)
    for i in range(0, len(Repository_List)):
        List_Item = str(Repository_List[i])
        File = open("storing/" + List_Item, "rb").read()
        List_Item = int(List_Item)
        List_Item = List_Item.to_bytes(20, byteorder='big')
        Owner.send(List_Item)
        Length = len(File)
        Length = Length.to_bytes(8, byteorder='big')
        Owner.send(Length)
        Owner.send(File)
    Owner.recv(1)

def HandlePulse(connection):
    connection.send("T".encode())

def TableUpdater():
    while True:
        time.sleep(15)
        UpdateTable()

def HandleABD(connection):
    global Successor
    suc_index, suc_ip, suc_port = TableBreaker(Successor)
    suc_ip = IntefyIP(suc_ip)
    suc_port = int(suc_port)
    suc_ip = suc_ip.to_bytes(4, byteorder='big')
    suc_port = suc_port.to_bytes(2, byteorder='big')
    connection.send(suc_ip)
    connection.send(suc_port)

def HandleClient(connection):
    clientConn, clientAddr = connection
    clientIP = clientAddr[0]
    connection = clientConn
    Request = connection.recv(3)
    Request = ByteToString(Request)
    if "INS" in Request:
        HandleInsert(connection)
    elif "PUL" in Request:
        HandlePulse(connection)
    elif "REM" in Request:
        HandleRemove(connection)
    elif "GET" in Request:
        HandleGet(connection)
    elif "EXI" in Request:
        HandleExist(connection)
    elif "OWN" in Request:
        HandleOwn(connection)
    elif "CON" in Request:
        HandleConnection(connection)
    elif "DIS" in Request:
        HandleDisconnect(connection)
    elif "ABD" in Request:
        HandleABD(connection)
    elif "INF" in Request:
        HandleInfo(connection)
        
def ListenForClient(listener):
    while True:
        threading.Thread(target=HandleClient, args=(listener.accept(),), daemon=True).start()

def HandleUser():
    Command = ""
    print("You will get a set of options for each command except Disconnect. Press the number and enter to choose your option.")
    print("All the files you receive or store yourself are in the '/repository' folder.")
    while Command != "6":
        print("[1] Insert")
        print("[2] Remove")
        print("[3] Get")
        print("[4] Exists")
        print("[5] Owns")
        print("[6] Disconnect")
        print("[7] Table Check")
        Command = input()
        if Command == "6":
            Disconnect()
            sys.exit()
            break
        elif Command == "7":
            global User
            global FingerTable
            global Successor
            global SuccessorsSuccessor
            print(User)
            print(Successor)
            print(SuccessorsSuccessor)
            #Table = GiveTable()
            for i in range(0, len(FingerTable)):
                print("INDEX: " + str(i))
                print(FingerTable[i])
        elif Command == "1":
            print("Now choose the file you have in the repository folder")
            Repository_List = os.listdir("repository")
            for i in range(0, len(Repository_List)):
                List_Item = str(Repository_List[i])
                print("[" + str(i) + "] " + List_Item)
            Wanted_File = int(input())
            #Send_File = open("repository/" + str(Repository_List[Wanted_File]), "r").read()
            Given = InsertFile(Repository_List[Wanted_File])
            print(Given)
        elif Command == "2":
            print("Type the file needed to be removed")
            Removing_File = input()
            Given = Remove(Removing_File)
            print(Given)
        elif Command == "3":
            print("What file do you want to get?")
            Get_File = input()
            Given = Get(Get_File)
            print(Given)
        elif Command == "4":
            print("What file do you want to check the existence of?")
            Exist_File = input()
            Given = Exists(Exist_File)
            print(Given)
        elif Command == "5":
            print("What file do you want the owner of? Make sure to include the file extension.")
            wanted_file = input()
            wanted_file = getHashIndex(wanted_file)
            Given, ip, port = findOwner(wanted_file)
            print(str(ip) + ":" + str(port))
        else:
            print("Try following direction better. That wasn't one of the number options. Either type '1','2', etc.")

def getLocalIPAddress():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

try:
    os.stat("storing")
except:
    os.mkdir("storing")

try:
    os.stat("repository")
except:
    os.mkdir("repository")
listener = socket(AF_INET, SOCK_STREAM)
listener.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
listener.bind(('', 0))
listener.listen()
myPort=(listener.getsockname()[1])
myIP = getLocalIPAddress()
print("Your IP and Port to give for others to join: " + str(myIP) + ":" + str(myPort))
myIndex = getHashIndex(str(myIP) + ":" + str(myPort))
print("Here's your index: " + str(myIndex))
Address = str(myIP) + str(myPort)
User = [myIndex, myIP, myPort]

print("If you want to join a swarm type their IP if not press ENTER")
IP = input()
if IP != "":
    #This is where the connection attempt occurs
    print("Type their port")
    Port = int(input())
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((IP, int(Port)))
    Confirmation = ""
    while Confirmation != "T":
        conn.send("CON".encode())
        #myIndex = myIndex.to_bytes(20, byteorder='big')
        #conn.send(myIndex)
        ip = IntefyIP(myIP)
        ip = ip.to_bytes(4, byteorder='big')
        port = int(myPort)
        port = port.to_bytes(2, byteorder='big')
        conn.send(ip)
        conn.send(port)
        Confirmation = conn.recv(1)
        Confirmation = ByteToString(Confirmation)
        if Confirmation == "N":
            FingerTable = [[getHashIndex(IP+":"+str(Port)), IP, Port]]
            Owner_Conn, theirIP, theirPort = findOwner(myIndex)
            conn = socket(AF_INET, SOCK_STREAM)
            conn.connect((theirIP, int(theirPort)))
            FingerTable = []
    suc_IP = recvAll(conn, 4)
    suc_IP = int.from_bytes(suc_IP, byteorder="big")
    suc_IP = StringifyIP(suc_IP)
    suc_port = recvAll(conn, 2)
    suc_port = int.from_bytes(suc_port, byteorder="big")
    suc_IP2 = recvAll(conn, 4)
    suc_IP2 = int.from_bytes(suc_IP2, byteorder="big")
    suc_IP2 = StringifyIP(suc_IP2)
    suc_port2 = recvAll(conn, 2)
    suc_port2 = int.from_bytes(suc_port2, byteorder="big")
    SuccessorsSuccessor = [getHashIndex(suc_IP2 + ":" + str(suc_port2)), suc_IP2, str(suc_port2)]
    Successor = [getHashIndex(suc_IP + ":" + str(suc_port)), suc_IP, str(suc_port)]
    num_Items = recvAll(conn, 8)
    num_Items = int.from_bytes(num_Items, byteorder="big")
    Items_Downloaded = 0
    while Items_Downloaded != num_Items:
        key = recvAll(conn, 20)
        key = int.from_bytes(key, byteorder="big")
        valSize = recvAll(conn, 8)
        valSize = int.from_bytes(valSize, byteorder="big")
        val = recvAll(conn, valSize)
        f = open(("storing/"+str(key)), "wb+")
        f.write(val)
        f.close()
        Items_Downloaded = Items_Downloaded + 1
    conn.send("T".encode())
    UpdateTable()
else:
    Successor = User
    SuccessorsSuccessor = User
    listener.listen()
    SuccessorsSuccessor = User

threading.Thread(target=TableUpdater, daemon=True).start()
threading.Thread(target=ListenForClient, args=(listener,), daemon=True).start()
threading.Thread(target=HandleUser, daemon=False).start()