from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')

def check_db():
    client = MongoClient(mongo_url)
    db = client['mj_dev']
    
    collections = db.list_collection_names()
    print(f'Collections in mj_dev: {collections}')
    
    # Check users collection
    if 'users' in collections:
        count = db['users'].count_documents({})
        print(f'Users in collection: {count}')
        users = list(db['users'].find({}, {'email': 1, 'name': 1}))
        for user in users:
            print(f"  - {user.get('email')}: {user.get('name')}")
    
    client.close()

check_db()
