def calculate_pi(precision):
	pi_estimate = 0
	denominator = 1
	sign = 1

	for i in range(1, precision * 100):  # More iterations for accuracy
		pi_estimate += sign * (4 / denominator)
		print(f"Крок {i}: π ≈ {pi_estimate:.{precision}f}"
		     )  # Intermediate value output

		denominator += 2
		sign *= -1  # Alternation of signs

	return round(pi_estimate, precision)


file_name = "output_pi_10.txt"
precision = 100

result = calculate_pi(precision)

print("Result:")
print(result)

with open(file_name, "w", encoding="utf-8") as file:
	file.write(result)
	file.write("\n")

print("The result is saved to a file" + file_name)
