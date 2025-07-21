#!/usr/bin/env python3
"""
Create a sample Excel file for testing the course upload functionality
"""

import pandas as pd

# Sample course data
sample_courses = {
    'title': [
        'Excel Test Course 1 - Python Basics',
        'Excel Test Course 2 - Web Development',
        'Excel Test Course 3 - Data Science',
        'Excel Test Course 4 - Machine Learning'
    ],
    'description': [
        'Learn Python programming fundamentals from scratch',
        'Build modern web applications with HTML, CSS, and JavaScript',
        'Analyze data using Python libraries like pandas and matplotlib',
        'Understand machine learning algorithms and applications'
    ],
    'url': [
        'https://example.com/python-basics',
        'https://example.com/web-development',
        'https://example.com/data-science',
        'https://example.com/machine-learning'
    ],
    'source': [
        'Excel Upload Test',
        'Excel Upload Test',
        'Excel Upload Test',
        'Excel Upload Test'
    ],
    'level': [
        'Beginner',
        'Beginner',
        'Intermediate',
        'Advanced'
    ],
    'points': [
        100,
        120,
        200,
        300
    ],
    'category': [
        'Programming',
        'Web Development',
        'Data Science',
        'Machine Learning'
    ],
    'difficulty': [
        'Easy',
        'Easy',
        'Medium',
        'Hard'
    ]
}

# Create DataFrame
df = pd.DataFrame(sample_courses)

# Save to Excel file
df.to_excel('sample_courses_upload.xlsx', index=False)

print("Sample Excel file created: sample_courses_upload.xlsx")
print(f"Contains {len(df)} test courses")
print("\nColumns included:")
for col in df.columns:
    print(f"  - {col}")

print("\nYou can now test the Excel upload functionality with this file.")
