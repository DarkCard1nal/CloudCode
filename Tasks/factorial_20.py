def factorial(n, step=1):
	if n == 0 or n == 1:
		print(f"Step {step}: {n}! = 1")
		return 1
	else:
		result = n * factorial(n - 1, step + 1)
		print(f"Step {step}: {n}! = {result}")
		return result


file_name = "output_factorial_20.txt"

result = factorial(20)

print("Result:")
print(result)

with open(file_name, "w", encoding="utf-8") as file:
	file.write(str(result))
	file.write("\n")

print("The result is saved to a file" + file_name)
