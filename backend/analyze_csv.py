#!/usr/bin/env python
import pandas as pd
import sys
import os

# Try different encodings
encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
df = None

for encoding in encodings:
    try:
        df = pd.read_csv('Antibiotics.csv', encoding=encoding)
        print(f'Successfully read with encoding: {encoding}')
        break
    except Exception as e:
        print(f'Failed with {encoding}: {e}')
        continue

if df is not None:
    # Clean up column names by stripping whitespace
    df.columns = df.columns.str.strip()
    
    # Show column names
    print('\nColumn names:')
    for col in df.columns:
        print(f'"{col}"')
    
    # Show unique conditions
    print('\n=== UNIQUE CONDITIONS ===')
    conditions = df['Condition'].dropna().unique()
    for condition in conditions:
        if isinstance(condition, str):
            print(f"'{condition.strip()}'")
        else:
            print(condition)

    print('\n=== UNIQUE SEVERITIES ===')
    severity_col = None
    for col in df.columns:
        if 'Severity' in col:
            severity_col = col
            break
    
    if severity_col:
        severities = df[severity_col].dropna().unique()
        for severity in severities:
            if isinstance(severity, str):
                print(f"'{severity.strip()}'")
            else:
                print(severity)

    print('\n=== UNIQUE CONDITION-SEVERITY COMBINATIONS ===')
    if severity_col:
        combinations = df[['Condition', severity_col]].dropna().drop_duplicates()
        for _, row in combinations.iterrows():
            condition = row['Condition'].strip() if isinstance(row['Condition'], str) else row['Condition']
            severity = row[severity_col].strip() if isinstance(row[severity_col], str) else row[severity_col]
            print(f'{condition} | {severity}')

    print('\n=== UNIQUE PATHOGENS (split by comma) ===')
    pathogen_col = None
    for col in df.columns:
        if 'Pathogens' in col:
            pathogen_col = col
            break
    
    if pathogen_col:
        all_pathogens = set()
        pathogen_data = df[pathogen_col].dropna()
        for pathogens_str in pathogen_data:
            if isinstance(pathogens_str, str):
                pathogens = [p.strip() for p in pathogens_str.split(',')]
                all_pathogens.update(pathogens)

        for pathogen in sorted(all_pathogens):
            print(f"'{pathogen}'")
            
    print('\n=== SAMPLE DATA (first 3 rows) ===')
    print(df.head(3).to_string())
else:
    print('Could not read CSV file with any encoding')
