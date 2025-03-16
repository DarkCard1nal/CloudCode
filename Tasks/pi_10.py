from math import pi

file_name = "output_pi_10.txt"

result = f"{pi:.10f}"

print("Result:")
print(result)

with open(file_name, "w", encoding="utf-8") as file:
	file.write(result)
	file.write("\n")

print("The result is saved to a file" + file_name)
