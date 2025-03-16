file_name = "output_addition.txt"

result = 2 + 3

print("Result:")
print(result)

with open(file_name, "w", encoding="utf-8") as file:
	file.write("2 + 3 = ")
	file.write(result)
	file.write("\n")

print("The result is saved to a file" + file_name)
