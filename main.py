import os 
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from config import system_prompt
# from functions.get_files_info import schema_get_files_info
# from functions.run_python_file import schema_run_python_file
# from functions.write_file import schema_write_file
# from functions.get_file_content import schema_get_file_content
from functions.call_function import *

def main():
    load_dotenv()

    verbose = "--verbose" in sys.argv
    args = []
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            args.append(arg)
    if not args:
        print("Ai code Assitant")
        print('\nUsage: python main.py "your prompt here" [--verbose]')
        print('Example: python main.py "How do i build a calculator app.')
        sys.exit(1)
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    user_prompt = " ".join(args)

    if verbose:
        print(f"User prompt: {user_prompt}\n")
    messages = [
        types.Content(role="user",parts=[types.Part(text=user_prompt)])
    ]
    try:
        for i in range(20):
            res = generate_content(client,messages,verbose)
            if not res:
                pass


    except Exception as e:
        return f"Error:{e}"

def generate_content(client,messages,verbose):
    available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_run_python_file
    ]
)
    response = client.models.generate_content(
        model='gemini-2.0-flash-001', 
        contents=messages,
        config = types.GenerateContentConfig(tools=[available_functions],system_instruction=system_prompt),
        
    )
    res_var = response.candidates
    for candidate in res_var:
        messages.append(candidate.content)
    if verbose:
        print("Prompt tokens:", response.usage_metadata.prompt_token_count)
        print("Response tokens:", response.usage_metadata.candidates_token_count)
    print("Response:")
    print(response.text)
    
    if not response.function_calls:
        return response.text

    function_responses = []
    for function_call_part in response.function_calls:
        function_call_result = call_function(function_call_part, verbose)
        if (
            not function_call_result.parts
            or not function_call_result.parts[0].function_response
        ):
            raise Exception("empty function call result")
        if verbose:
            print(f"-> {function_call_result.parts[0].function_response.response}")
        function_responses.append(function_call_result.parts[0])
        messages.append(types.Content(function_responses,role="user"))

    if not function_responses:
        raise Exception("no function responses generated, exiting.")

    
if __name__ == "__main__":
    main()
