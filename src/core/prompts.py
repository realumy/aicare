import os
import anthropic


STRUCT_PATIENT_INPUT = {"system" : """
You are an AI assistant with expertise in medecine.
Your task is to take text provided by a patient describing symptoms,
to extract relevant information and to output a synthesized, structered
text for the doctor. The output should be summarize the information
as bullet points and suggest to the doctor questions to ask the patient
as bullet points too.

The two blocks, should be separated by two line returns.
""",

"messages" : [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": None,
        }
      ]
    }
  ]
}

client = anthropic.Anthropic(
  api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


def generate_summary_and_questions(text):
    template = STRUCT_PATIENT_INPUT.copy()
    template["messages"][0]["content"][0]["text"] = text

    message = client.messages.create(
      model="claude-3-5-sonnet-20241022",
      max_tokens=2000,
      temperature=1,
      **template
    ) 

    response = message.content[0].text

    summary, questions = response.split("\n\n", 1)
    summary = [t for t in summary.split("\n")[1:] if t]
    questions = [t for t in questions.split("\n")[1:] if t]
    return summary, questions


