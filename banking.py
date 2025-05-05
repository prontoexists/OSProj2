import threading
import time
import random
from queue import Queue

tell_val = 3
cust_val = 50
pLock = threading.Lock()
safeDoorThr = threading.Semaphore(2)
safeOpenThr = threading.Event()
safeThr = threading.Semaphore(2)
manThr = threading.Semaphore(1)
CustQ = Queue()
TellQ = Queue()

class Teller(threading.Thread):
    def __init__(self, tid):
        super().__init__()
        self.tid = tid

    def run(self):
        with pLock:
            print(f"Teller {self.tid} [Teller {self.tid}]: is ready")
        TellQ.put(self)

        safeOpenThr.set()
        while True:
            try:
                custI = CustQ.get(timeout=1)
            except:
                break

            custId, actionVal, thrS = custI
            with pLock:
                print(f"Teller {self.tid} [Customer {custId}]: called Customer")

            ques, respo, finishS, exitC = thrS
            ques.release()
            respo.acquire()

            if actionVal == "Withdraw":
                with pLock:
                    print(f"Teller {self.tid} [Customer {custId}]: visits manager")
                    print(f"Teller {self.tid} [Customer {custId}]: informs manager")
                manThr.acquire()
                with pLock:
                    print(f"Teller {self.tid} [Customer {custId}]: finished with manager")
                manThr.release()

            with pLock:
                print(f"Teller {self.tid} [Customer {custId}]: going to safe")
            safeThr.acquire()
            with pLock:
                print(f"Teller {self.tid} [Customer {custId}]: using safe")
            with pLock:
                print(f"Teller {self.tid} [Customer {custId}]: finish with safe")
                print(f"Teller {self.tid} [Customer {custId}]: transaction complete")

            safeThr.release()
            finishS.release()
            exitC.acquire()

            TellQ.put(self)

class Customer(threading.Thread):
    def __init__(self, cid):
        super().__init__()
        self.cid = cid

    def run(self):
        actionVal = random.choice(["Deposit", "Withdraw"])
        safeDoorThr.acquire()
        safeOpenThr.wait()

        with pLock:
            print(f"Customer {self.cid} [Customer {self.cid}]: enters bank")

        teller = TellQ.get()
        with pLock:
            print(f"Customer {self.cid} [Teller {teller.tid}]: selects teller")

        ques = threading.Semaphore(0)
        respo = threading.Semaphore(0)
        finishS = threading.Semaphore(0)
        exitC = threading.Semaphore(0)

        CustQ.put((self.cid, actionVal, (ques, respo, finishS, exitC)))
        ques.acquire()

        with pLock:
            print(f"Customer {self.cid} [Teller {teller.tid}]: gives transaction: {actionVal}")
        respo.release()
        finishS.acquire()
        with pLock:
            print(f"Customer {self.cid} [Teller {teller.tid}]: transaction complete")
            print(f"Customer {self.cid} [Teller {teller.tid}]: leaves bank")
        exitC.release()
        safeDoorThr.release()

tellers = [Teller(i) for i in range(tell_val)]
for t in tellers:
    t.start()

while TellQ.qsize() < tell_val:
    time.sleep(0.01)

customers = [Customer(i) for i in range(cust_val)]
for c in customers:
    c.start()

for c in customers:
    c.join()

with pLock:
    print("MAIN - [BANK -]: Bank Closed.")
