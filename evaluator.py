import google.generativeai as genai
import json
import re
import base64

def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)

EVAL_PROMPT = """You are an expert evaluator for EMRS (Eklavya Model Residential Schools) TGT/PGT Computer Science teacher recruitment exam (ESSE).

Evaluate the following student answer strictly and fairly.

**Question:** {question}

**Maximum Marks:** {max_marks}

**Evaluation Criteria:**
- Technical accuracy and correctness
- Completeness of the answer
- Clarity and coherence of explanation
- Use of proper terminology
- Relevant examples (if applicable)

Provide your evaluation in the following JSON format ONLY (no extra text):
{{
  "score": <number between 0 and {max_marks}, decimals allowed like 2.5>,
  "feedback": "<2-3 sentences of constructive feedback explaining the score, what was correct and what was missing>"
}}

Be strict but fair. Award marks proportionally based on completeness and accuracy."""


def evaluate_answer(question_text: str, student_answer: str, max_marks: int = 4) -> dict:
    """Evaluate a plain text answer using Gemini."""
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = EVAL_PROMPT.format(question=question_text, max_marks=max_marks)
    full_prompt = prompt + f"\n\n**Student's Answer:** {student_answer}"

    try:
        response = model.generate_content(full_prompt)
        return _parse_response(response.text, max_marks)
    except Exception as e:
        return {"score": 0, "feedback": f"Evaluation error: {str(e)}"}


def evaluate_image_answer(question_text: str, image_bytes: bytes, max_marks: int = 4) -> dict:
    """Evaluate a handwritten answer image using Gemini Vision."""
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = EVAL_PROMPT.format(question=question_text, max_marks=max_marks)
    full_prompt = prompt + "\n\n**Student's Answer:** The student has submitted a handwritten answer. Please read the handwritten text in the image carefully and evaluate it based on the criteria above."

    # Detect image type from bytes header
    if image_bytes[:4] == b'\x89PNG':
        mime_type = "image/png"
    elif image_bytes[:2] == b'\xff\xd8':
        mime_type = "image/jpeg"
    elif image_bytes[:4] == b'GIF8':
        mime_type = "image/gif"
    elif image_bytes[:4] == b'RIFF':
        mime_type = "image/webp"
    else:
        mime_type = "image/jpeg"  # default fallback

    image_part = {
        "mime_type": mime_type,
        "data": base64.b64encode(image_bytes).decode("utf-8")
    }

    try:
        response = model.generate_content([
            full_prompt,
            {"inline_data": image_part}
        ])
        return _parse_response(response.text, max_marks)
    except Exception as e:
        return {"score": 0, "feedback": f"Image evaluation error: {str(e)}"}


def _parse_response(text: str, max_marks: int) -> dict:
    """Parse Gemini JSON response into score and feedback."""
    try:
        text = text.strip()
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            score  = float(result.get("score", 0))
            score  = max(0.0, min(score, float(max_marks)))
            return {
                "score": score,
                "feedback": result.get("feedback", "No feedback provided.")
            }
        return {"score": 0, "feedback": "Could not parse evaluation response."}
    except Exception as e:
        return {"score": 0, "feedback": f"Parse error: {str(e)}"}