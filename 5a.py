from pymongo import MongoClient
from bson import ObjectId
from tqdm import tqdm
import json
import os
import subprocess
import sys
import glob

class SpotifyAutograder:
    def __init__(self):
        self.client = MongoClient(
            "mongodb+srv://banghao2:cbh1023@autograder.93xjn.mongodb.net/?retryWrites=true&w=majority&appName=Autograder"
        )
        self.db = self.client['test_spotify_db']
        
    def setup_test_data(self):
        self.db.songs.drop()
        self.db.albums.drop()
        
        thriller_songs = [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "name": "Baby Be Mine",
                "artist": "Michael Jackson",
                "year": "1982",
                "duration": 260000
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439012"),
                "name": "The Girl Is Mine",
                "artist": "Michael Jackson",
                "year": "1982",
                "duration": 222000
            },
        ]
        
        self.db.songs.insert_many(thriller_songs)
        
        thriller_album = {
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "name": "Thriller",
            "artist": "Michael Jackson",
            "year": "1982",
            "songs": [song["_id"] for song in thriller_songs]
        }
        
        self.db.albums.insert_one(thriller_album)
        
    def grade_submission(self, submission_path):
        try:
            expected_result = [
                {"name": "Baby Be Mine"},
                {"name": "The Girl Is Mine"},
            ]

            with open(submission_path, 'r') as f:
                student_code = f.read()
            
            modified_code = f"""{student_code.split(';', 1)[1]}

print("RESULT_START");
print(JSON.stringify(album_songs));
print("RESULT_END");"""
            
            temp_file = "temp_query_5a.js"
            with open(temp_file, 'w') as f:
                f.write(modified_code)
            
            result = subprocess.run(
                ['mongosh', 
                 'mongodb+srv://banghao2:cbh1023@autograder.93xjn.mongodb.net/test_spotify_db?retryWrites=true&w=majority&appName=Autograder',
                 '--file', temp_file],
                capture_output=True,
                text=True,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            print("Return code:", result.returncode)
            
            os.remove(temp_file)
            
            student_result = self.parse_mongo_output(result.stdout)
            
            return self.compare_results(expected_result, student_result)
            
        except Exception as e:
            return {
                'score': 0,
                'feedback': f"Error executing submission: {str(e)}"
            }
    
    def parse_mongo_output(self, output):
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
    
    def compare_results(self, expected, actual):
        if actual is None:
            return {
                'score': 0,
                'feedback': "Could not parse query results"
            }
        
        if len(expected) != len(actual):
            return {
                'score': 2,
                'feedback': f"Expected {len(expected)} songs, got {len(actual)}"
            }
        
        expected_names = {song['name'] for song in expected}
        actual_names = {song.get('name') for song in actual}
        
        if expected_names == actual_names:
            return {
                'score': 5,
                'feedback': "Perfect! All song names match."
            }
        else:
            missing = expected_names - actual_names
            extra = actual_names - expected_names
            feedback = []
            if missing:
                feedback.append(f"Missing songs: {', '.join(missing)}")
            if extra:
                feedback.append(f"Extra songs: {', '.join(extra)}")
            
            return {
                'score': 3,
                'feedback': " ".join(feedback)
            }
    
    def grade_folder(self, submissions_folder):
        results = {}
        submission_files = glob.glob(os.path.join(submissions_folder, "*query.js"))
        print(f"Grading {len(submission_files)} submissions")
        
        for submission_path in tqdm(submission_files, desc="Grading submissions"):
            student_id = ''.join(char for char in os.path.basename(submission_path).split('question')[0].rstrip("_") if char.isalpha() or char == '_')
            results[student_id] = self.grade_submission(submission_path)
        
        return results

def main():
    if len(sys.argv) != 2:
        print("Usage: python autograder.py <path_to_submissions_folder>")
        sys.exit(1)
        
    submissions_folder = sys.argv[1]
    grader = SpotifyAutograder()
    
    grader.setup_test_data()
    
    results = grader.grade_folder(submissions_folder)
    
    print("\nGrading Results:")
    print("-" * 40)
    for student_id, result in results.items():
        print(f"\nStudent: {student_id}")
        print(f"Score: {result['score']}/5")
        print(f"Feedback: {result['feedback']}")

    with open('results_5a.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()