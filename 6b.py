from tqdm import tqdm
import json
import os
import subprocess
import sys
import glob

class CPSAutograder:
    def __init__(self):
        pass
        
    def setup_test_data(self):
        """No database setup needed for this problem"""
        pass
        
    def grade_submission(self, submission_path):
        """Grade a student's CPS.js submission"""
        try:
            # Read student's submission
            with open(submission_path, 'r') as f:
                student_code = f.read()
            
            # Create a test wrapper that will execute the student's code
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

// Mock XMLHttpRequest
class MockXMLHttpRequest {{
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
        // Simulate async response
        setTimeout(() => {{
            this.responseText = '{{"color": "orange"}}';
            if (this.listeners.load) {{
                this.listeners.load();
            }}
        }}, 100);
    }}
}}

// Replace XMLHttpRequest with mock
global.XMLHttpRequest = MockXMLHttpRequest;

// Student's code
{student_code}

// Wait for async operations and print result
setTimeout(() => {{
    console.log("RESULT_START");
    console.log(JSON.stringify({{ 
        buttonColor: buttonColor,
        hasError: hasError
    }}));
    console.log("RESULT_END");
}}, 200);"""
            
            # Save test wrapper to temporary file
            temp_file = "temp_test_6b.js"
            with open(temp_file, 'w') as f:
                f.write(test_wrapper)
            
            # Execute using Node.js
            result = subprocess.run(
                ['node', temp_file],
                capture_output=True,
                text=True
            )
            
            # Clean up
            os.remove(temp_file)
            
            # Parse the output
            student_result = self.parse_output(result.stdout)
            
            return self.evaluate_result(student_result, submission_path)
            
        except Exception as e:
            return {
                'score': 0,
                'feedback': f"Error executing submission: {str(e)}"
            }
    
    def parse_output(self, output):
        """Parse Node.js output to extract results"""
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
        """Evaluate the student's solution"""
        if result is None:
            return {
                'score': 0,
                'feedback': "Could not execute or parse the solution"
            }
        
        if result.get('hasError'):
            return {
                'score': 1,
                'feedback': "Your code threw an error during execution. Make sure you're handling the color value correctly."
            }

        if result.get('buttonColor') != 'orange':
            return {
                'score': 2,
                'feedback': "The button color was not correctly set to 'orange'. Make sure you're using CPS correctly to handle the asynchronous response."
            }
            
        # More thorough CPS style checking
        with open(submission_path, 'r') as f:
            code = f.read().lower()
            has_continuation = 'function(' in code and ('ret(' in code or 'continuation(' in code)
            has_callback = 'addeventlistener' in code and 'load' in code
            
            if not has_continuation:
                return {
                    'score': 3,
                    'feedback': "Solution works but doesn't appear to use proper CPS style. Make sure you're using continuation functions with explicit callbacks."
                }
            
            if not has_callback:
                return {
                    'score': 4,
                    'feedback': "Solution uses CPS but might not be handling the XMLHttpRequest callback correctly."
                }
        
        return {
            'score': 5,
            'feedback': "Perfect! Your solution correctly implements CPS and handles the async color change."
        }
    
    def grade_folder(self, submissions_folder):
        """Grade all CPS.js files in the given folder"""
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
        
    submissions_folder = sys.argv[1]
    grader = CPSAutograder()
    
    # Grade all submissions
    results = grader.grade_folder(submissions_folder)
    
    # Print results
    print("\nGrading Results:")
    print("-" * 40)
    for student_id, result in results.items():
        print(f"\nStudent: {student_id}")
        print(f"Score: {result['score']}/5")
        print(f"Feedback: {result['feedback']}")

    # Save results to a JSON file
    with open('results_6b.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()
