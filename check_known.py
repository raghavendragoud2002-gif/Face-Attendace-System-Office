import pickle
import os

known_path = 'data/known_orb.pkl'
if os.path.exists(known_path):
    with open(known_path, 'rb') as f:
        known = pickle.load(f)
    
    print(f"Known faces in database: {len(known)}")
    for person in known:
        print(f"  - Name: {person['name']}")
        # Extract ID from name
        parts = person['name'].split('_')
        if parts[0].isdigit():
            print(f"    Employee ID: {parts[0]}")
else:
    print("Known faces file not found!")
