from cirriculumn import generate_curriculum_pdf
from model_handler import LocalLLM
from prompts import EDUCATIONAL_PROMPTS

# Example input
example_request = {
    "grade": "6th Grade",
    "subject": "Mathematics",
    "topic": "Fractions and Decimals",
    "duration_value": 3,
    "duration_unit": "months",
    "language": "English",
    "teaching_style": "Visual"
}

# Generate curriculum prompt
prompt = EDUCATIONAL_PROMPTS["Learn Concept"].format(
    language=example_request["language"],
    grade=example_request["grade"],
    subject=example_request["subject"],
    topic=example_request["topic"]
)

# Use LLM to generate content
llm = LocalLLM()
response = llm.generate(prompt, teaching_style=example_request["teaching_style"])

# Compile the curriculum PDF
curriculum_content = "\n".join([line.decode('utf-8') for line in response])
pdf_content = generate_curriculum_pdf(
    curriculum_content,
    example_request["grade"],
    example_request["subject"],
    f"{example_request['duration_value']} {example_request['duration_unit']}"
)

# Save the PDF
with open("examples/example_curriculum_output.pdf", "wb") as f:
    f.write(pdf_content)

print("Curriculum generated successfully!")
