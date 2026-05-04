import os
import subprocess
from google import genai
from google.genai import types

import time

# Initialize the client using the new SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def ask_llm(prompt: str, system_prompt: str = "You are an expert Python testing engineer.") -> str:
    """Send a prompt to Gemini and return the code."""
    
    max_api_retries = 5
    for attempt in range(max_api_retries):
        try:
            # Generate the response using the new syntax
            response = client.models.generate_content(
                model="gemini-2.5-flash", # Swapped to standard 2.5-flash for maximum stability
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2, # Keep it low for deterministic code generation
                )
            )
            
            # Strip markdown code blocks if the LLM includes them
            content = response.text
            return content.replace("```python", "").replace("```", "").strip()
            
        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s, 16s
                print(f"API overloaded (Error 503/429). Waiting {wait_time} seconds and retrying... (Attempt {attempt + 1}/{max_api_retries})")
                time.sleep(wait_time)
            else:
                # If it's a different error (e.g. invalid API key), raise it further
                raise e
    
    raise Exception(f"Failed after {max_api_retries} attempts due to busy Google servers. Please try again later.")

def run_test(test_file_path: str, test_name: str) -> tuple[bool, str]:
    """Run pytest on a specific test and return (Success, Output)."""
    cmd = ["pytest", f"{test_file_path}::{test_name}", "--tb=short"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout + result.stderr

def generate_passing_test(method_name: str, method_source: str, branch_condition: str, test_file_path: str, test_name: str) -> str:
    """The Agent Loop: Write test -> Run test -> Fix test -> Return code"""
    
    prompt = f"""
    Write a pytest function named `{test_name}` for the method `{method_name}`.
    Your specific goal is to write setup code and mock arguments that will cause this specific condition to evaluate to TRUE:
    Condition: `{branch_condition}`

    Here is the source code of the method to help you understand the required inputs:
    {method_source}

    Return ONLY the raw Python code for the test function. Assume `env` is provided by a pytest fixture.
    """

    max_retries = 3
    current_code = ""

    for attempt in range(max_retries):
        print(f"Agent Attempt {attempt + 1}/{max_retries} for {test_name}...")
        
        # 1. ACT: Get code from LLM
        current_code = ask_llm(prompt)
        
        # 2. Inject the code into your test file temporarily to test it
        with open(test_file_path, "a") as f:
            f.write("\n" + current_code + "\n")
            
        # 3. OBSERVE: Run the test
        success, error_output = run_test(test_file_path, test_name)
        
        if success:
            print(f"Success! Generated passing test for {branch_condition}")
            return current_code
            
        # 4. REASON: If it failed, prepare the feedback prompt for the next loop
        print(f"Test failed. Asking AI to fix it...")
        prompt += f"\n\nYour previous code failed with this error:\n{error_output}\n\nPlease fix the test and return the corrected Python code."

    print(f"Agent failed to generate a passing test after {max_retries} attempts.")
    return f"# TODO: Agent failed to generate test for {branch_condition}\n" + current_code