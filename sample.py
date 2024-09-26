import random
import json

# File paths
input_file = "data_full.jsonl"
output_file = "data.jsonl"

# Open the input file and read all lines
with open(input_file, "r") as file:
    lines = file.readlines()

# Randomly sample 500 lines
sampled_lines = random.sample(lines, 500)

# Write the sampled lines to a new file
with open(output_file, "w") as file:
    for line in sampled_lines:
        file.write(line)

print(f"Sampled 500 lines and saved to {output_file}")
