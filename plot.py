import json
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

def plot_assignment_results(results_file, title=None):
    # Read the JSON file
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Count the frequency of each score
    scores = [student_data['score'] for student_data in results.values()]
    score_counts = Counter(scores)
    
    # Prepare data for plotting
    unique_scores = sorted(score_counts.keys())
    frequencies = [score_counts[score] for score in unique_scores]
    
    # Create the bar plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(unique_scores, frequencies)
    
    # Customize the plot
    plt.title(title or f'Score Distribution - {results_file}')
    plt.xlabel('Score')
    plt.ylabel('Number of Students')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')
    
    # Set x-axis ticks to only show the actual scores
    plt.xticks(unique_scores)
    
    # Add grid for better readability
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)

    plt.savefig(f'images/{results_file}.png')
    
    return plt

# Example usage for multiple files
result_files = {
    'Question 5a': 'results_5a.json',
    'Question 6b': 'results_6b.json'
}

# Create a plot for each result file
for question, file_path in result_files.items():
    plot = plot_assignment_results(file_path, f'Score Distribution - {question}')
    plot.show()

# Calculate and print some statistics
def print_statistics(results_file, question_name):
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    scores = [student_data['score'] for student_data in results.values()]
    total_students = len(scores)
    avg_score = np.mean(scores)
    median_score = np.median(scores)
    
    print(f"\nStatistics for {question_name}:")
    print(f"Total students: {total_students}")
    print(f"Average score: {avg_score:.2f}")
    print(f"Median score: {median_score}")
    print(f"Score distribution:")
    for score, count in sorted(Counter(scores).items()):
        percentage = (count/total_students) * 100
        print(f"Score {score}: {count} students ({percentage:.1f}%)")

# Print statistics for each file
for question, file_path in result_files.items():
    print_statistics(file_path, question)
