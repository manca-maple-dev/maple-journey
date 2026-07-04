from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')

def list_users():
    client = MongoClient(mongo_url)
    db = client['mj_dev']
    users = db['users']
    
    all_users = list(users.find({}, {'email': 1, 'profile_completed': 1, 'name': 1}))
    print(f'Found {len(all_users)} users:')
    for user in all_users:
        print(f"  - {user.get('email')}: profile_completed={user.get('profile_completed')}, name={user.get('name')}")
    
    client.close()

list_users()
