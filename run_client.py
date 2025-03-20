from Client.client import CloudComputeClient

if __name__ == "__main__":
	client = CloudComputeClient()

	# Sending files one by one
	client.send_sequential()

	# Sending files in parallel
	client.send_parallel()

	# Sending infinite task
	client.send_single_task("Tasks/.infinite_task.py")
