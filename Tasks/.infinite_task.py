import time


def infinite_task():
	"""An infinite task with the output of the time for each step."""
	start_time = time.time()

	step = 0
	while True:
		elapsed_time = (time.time() - start_time) * 1000
		print(f"Step {step}: Execution time {elapsed_time:.2f} ms")
		with open(f"{step}.txt", "w", encoding="utf-8") as file:
			file.write(f"Step {step}: Execution time {elapsed_time:.2f} ms")

		time.sleep(0.1)  # Simulate 0.1 second delay (can be changed)
		step += 1


infinite_task()
