from Client.client import CloudComputeClient
from time import time, sleep
from threading import Thread

DURATION = 1200
INTERVAL = 2

# Sending files one by one
def send_one_by_one():
	start_time = time()
	while time() - start_time < DURATION:
		client.send_sequential()
		sleep(INTERVAL)

# Sending files in parallel
def send_in_parallel():
	start_time = time()
	while time() - start_time < DURATION:
		client.send_parallel()
		sleep(INTERVAL)

# Sending infinite task
def send_infinite_task():
	start_time = time()
	while time() - start_time < DURATION:
		client.send_single_task("Tasks/.infinite_task.py")
		sleep(INTERVAL)

if __name__ == "__main__":
	client = CloudComputeClient()

	t1 = Thread(target=send_one_by_one)
	t2 = Thread(target=send_in_parallel)
	t3 = Thread(target=send_infinite_task)

	t1.start()
	t2.start()
	t3.start()

	t1.join()
	t2.join()
	t3.join()
