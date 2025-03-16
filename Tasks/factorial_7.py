import math

file_name = "output_factorial_7.txt"

result = math.factorial(7)

print("Result:")
print(result)

with open(file_name, "w", encoding="utf-8") as file:
	file.write(result)
	file.write("\n")

print("The result is saved to a file" + file_name)
