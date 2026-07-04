from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')

def update_user():
    client = MongoClient(mongo_url)
    db = client['mj_dev']
    users = db['users']
    
    # Update the test user
    result = users.update_one(
        {'email': 'newuser@test.ca'},
        {'$set': {'profile_completed': True}}
    )
    print(f'Updated {result.modified_count} user(s)')
    
    # Verify
    user = users.find_one({'email': 'newuser@test.ca'})
    print(f'Profile completed: {user.get("profile_completed")}')
    client.close()

update_user()
