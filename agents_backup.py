#agents.py

import os
import csv
from prompts import *
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Set up the API key
if not os.getenv("GROQ_API_KEY"):
    if not os.getenv("OPENAI_API_KEY"):
        if int(input("Define de llm provider (0 - OpenAI or 1 - Groq): ")):
            print("\nGroq API selected.")
            os.environ["GROQ_API_KEY"] = input("\nPlease enter your Groq API key: ")
            client = Groq()   # Groq API
            MODEL = "llama3-8b-8192"
        else:
            print("\nOpenAI API selected.")
            os.environ["OPENAI_API_KEY"] = input("\nPlease enter your OpenAI API key: ")
            client = OpenAI()   # Open AI ChatGPT
            MODEL = "gpt-3.5-turbo"

else:
    client = Groq()   # Groq API
    MODEL = "llama3-8b-8192"   
      
# Function to read CSV file from the user
def read_csv(file_path):
    data = []
    with open(file_path, "r", newline="") as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            data.append(row)
    return data

# Function to save generated data to a new CSV file
def save_to_csv(data, output_file, headers=None):
    mode = 'w' if headers else 'a'
    with open(output_file, mode, newline="") as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        for row in csv.reader(data.splitlines()):
            writer.writerow(row)

# Create the Analyzer Agent
def analyzer_agent(sample_data):
    message = client.chat.completions.create(
        model=MODEL,
        max_tokens=400,
        temperature=0.1,
        messages=[
            {"role": "user", "content": ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": ANALYZER_USER_PROMPT.format(sample_data=sample_data)}
        ]
    )
    return message.choices[0].message.content

# Create the Generator Agent
def generator_agent(analysis_result, sample_data, num_rows=30):
    message = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        temperature=1,
        messages=[
            {"role": "user", "content": GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": GENERATOR_USER_PROMPT.format(
                num_rows=num_rows,
                analysis_result=analysis_result,
                sample_data=sample_data
                )
            }
        ]
    )
    return message.choices[0].message.content

# Main execution flow

# Get input from the user
file_path = input("\nEnter the name of your CSV file:")
file_path = os.path.join('app/data', file_path)
desired_rows = int(input("Enter the number of rows you want in the new dataset: "))

sample_data = read_csv(file_path)
sample_data_str = "\n".join([",".join(row) for row in sample_data]) #Converts 2D list to a single strin g

print("\n Launching team of Agents...")
# Analyze the sample data using the Analyzer Agent
analysis_result = analyzer_agent(sample_data_str)
print("\n### Analyzer Agent output: ###\n")
print(analysis_result)
print("\n--------------------------------------------\n\nGenerating new data...")

# Caminho do diretório mapeado no contêiner
mapped_directory = "./app/data"

# Set up the output file
output_file = os.path.join(mapped_directory, "new_dataset.csv")
headers = sample_data[0]
# Create the output file with headers
save_to_csv("", output_file, headers)

batch_size = 30 # Number of rows to generate in each batch
generated_rows = 0 # Counter to keep track of how many rows have been generated

# Generate data in batches until we reach the desired number of rows
while generated_rows < desired_rows:
    # Calculate how many rows to generate in this batch
    rows_to_generate = min(batch_size, desired_rows - generated_rows)
    # Generate a batch of data using the Generator Agent
    generated_data = generator_agent(analysis_result, sample_data_str, rows_to_generate)
    # Append the generated data to the output file
    save_to_csv(generated_data, output_file)
    # Update the count of generated rows
    generated_rows += rows_to_generate
    # Print progress update
    print(f"Generated {generated_rows} rows out of {desired_rows}" )

# Inform the user that we process is complete    
print(f"\nGenerated data has been saved to {output_file}")

    