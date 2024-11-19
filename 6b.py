from tqdm import tqdm
import json
import os
import subprocess
import sys
import glob
import time

class CPSAutograder:
    def __init__(self):
        pass
        
    def grade_submission(self, submission_path):
        try:
            with open(submission_path, 'r') as f:
                student_code = f.read()
            
            test_wrapper = f"""let buttonColor = null;
let hasError = false;

// Mock the setButtonColor function
function setButtonColor(color) {{
    try {{
        if (typeof color !== 'string') {{
            throw new Error('Invalid color type');
        }}
        buttonColor = color;
    }} catch (e) {{
        hasError = true;
        console.error(e);
    }}
}}

// Provide XMLHttpRequest implementation using fetch
class XMLHttpRequest {{
    constructor() {{
        this.listeners = {{}};
    }}

    addEventListener(event, callback) {{
        this.listeners[event] = callback;
    }}

    open(method, url) {{
        this.method = method;
        this.url = url;
    }}

    send() {{
        fetch(this.url)
            .then(response => response.json())
            .then(data => {{
                this.responseText = JSON.stringify(data);
                if (this.listeners['load']) {{
                    this.listeners['load']();
                }}
            }})
            .catch(error => {{
                if (this.listeners['error']) {{
                    this.listeners['error'](error);
                }}
            }});
    }}
}}

// Student's code
try {{
    {student_code.replace("this.responseText", "req.responseText")}
}} catch (e) {{
    hasError = true;
    console.error(e);
}}

// Wait for async operations and print result
setTimeout(() => {{
    console.log("RESULT_START");
    console.log(JSON.stringify({{ 
        buttonColor: buttonColor,
        hasError: hasError
    }}));
    console.log("RESULT_END");
}}, 1000);  // Increased timeout to allow for real server response""".replace(
                "/getColor", "http://localhost:8080/getColor"
            )
            
            temp_file = "temp_test_6b.js"
            with open(temp_file, 'w') as f:
                f.write(test_wrapper)
            
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )

            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("Return code:", result.returncode)
            
            os.remove(temp_file)
            
            student_result = self.parse_output(result.stdout)
            
            return self.evaluate_result(student_result, submission_path)
            
        except Exception as e:
            return {
                'score': 0,
                'feedback': f"Error executing submission: {str(e)}"
            }
    
    def parse_output(self, output):
        try:
            start_marker = "RESULT_START"
            end_marker = "RESULT_END"
            
            start_idx = output.find(start_marker)
            if start_idx == -1:
                return None
                
            end_idx = output.find(end_marker)
            if end_idx == -1:
                return None
                
            result_json = output[start_idx + len(start_marker):end_idx].strip()
            return json.loads(result_json)
            
        except Exception as e:
            print(f"Error parsing output: {e}")
            return None
    
    def evaluate_result(self, result, submission_path):
        accuracy_score = 0
        formatting_score = 0
        feedback = ""

        if result is None:
            return {
                'score': 0,
                'feedback': "Could not execute or parse the solution"
            }
        
        if result.get('hasError'):
            return {
                'score': 0,
                'feedback': "Your code threw an error during execution. Make sure you're handling the color value correctly."
            }

        if result.get('buttonColor') != 'orange':
            feedback += "The button color was not correctly set to 'orange'. Make sure you're using CPS correctly to handle the asynchronous response."
            accuracy_score = 1
        
        if result.get('buttonColor') == 'orange' and not result.get('hasError'):
            with open(submission_path, 'r') as f:
                code = f.read()

                has_inline_callback = any([
                    "addEventListener('load', function" in code,
                    'addEventListener("load", function' in code,
                    "addEventListener('load', (" in code,
                    'addEventListener("load", (' in code,
                    "addEventListener('load',function" in code,
                    'addEventListener("load",function' in code
                ])

                accuracy_score = 2

                if has_inline_callback:
                    formatting_score = 2
                    feedback += " Solution works but uses inline callbacks. For better CPS style, define your continuation function separately."
                else:
                    formatting_score = 3
                    feedback += "Perfect! Your solution correctly implements CPS and handles the async color change."
                    
        return {
            'score': accuracy_score + formatting_score,
            'feedback': feedback
        }
    
    def grade_folder(self, submissions_folder):
        results = {}
        submission_files = glob.glob(os.path.join(submissions_folder, "*CPS.js"))
        print(f"Grading {len(submission_files)} submissions")
        
        for submission_path in tqdm(submission_files, desc="Grading submissions"):
            student_id = ''.join(char for char in os.path.basename(submission_path).split('question')[0].strip("_") if char.isalpha() or char == '_')
            results[student_id] = self.grade_submission(submission_path)
        
        return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python 6b.py <path_to_submissions_folder>")
        sys.exit(1)
    
    server_process = subprocess.Popen([sys.executable, '6b_server.py'])
    try:
        time.sleep(1)
        
        submissions_folder = sys.argv[1]
        grader = CPSAutograder()
        
        results = grader.grade_folder(submissions_folder)
        
        print("\nGrading Results:")
        print("-" * 40)
        for student_id, result in results.items():
            print(f"\nStudent: {student_id}")
            print(f"Score: {result['score']}/5")
            print(f"Feedback: {result['feedback']}")

        with open('results_6b.json', 'w') as f:
            json.dump(results, f, indent=4)
    
    finally:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
