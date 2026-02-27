import os
from openai import OpenAI

# Load your API key (replace with your key or use environment variable)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("Welcome to the simplest AI workflow auditor!")
print("Type 'quit' to exit.\n")

while True:
    workflow = input("Enter a workflow step to check: ")

    if workflow.lower() == "quit":
        break

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that checks if a workflow is clear and logical."},
            {"role": "user", "content": workflow}
        ]
    )

    print("\nAI Audit Result:")
    print(response.choices[0].message["content"])
    print("\n" + "-" * 50 + "\n")
``
