import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.database import db

def remove_first_user():
    """Script to remove the first user from the database."""
    print("🗑️ AI Assistant - Remove First User")
    print("=" * 50)

    # Check if users exist
    existing_users = list(db.db.users.find().limit(1))
    if not existing_users:
        print("❌ No users found in the database.")
        return

    first_user = existing_users[0]
    user_id = str(first_user['_id'])
    username = first_user['username']
    
    # Confirm deletion
    confirm = input(f"Are you sure you want to remove the user '{username}'? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ User removal cancelled.")
        return

    try:
        # Remove the first user
        db.db.users.delete_one({'_id': first_user['_id']})
        print(f"✅ User '{username}' has been removed successfully!")
    
    except Exception as e:
        print(f"❌ Error removing user: {e}")

if __name__ == "__main__":
    remove_first_user()
