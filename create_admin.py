import sys
import os
from datetime import datetime
import getpass

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the db object from your database module
from db.database import db

def create_user(role):
    """Interactive function to create a user."""
    print(f"\nCreating {role} account...")
    
    username = input("Enter username: ").strip()
    email = input("Enter email: ").strip()
    full_name = input("Enter full name: ").strip()
    
    while True:
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords don't match. Please try again.")
            continue
        
        if len(password) < 6:
            print("❌ Password must be at least 6 characters long.")
            continue
        
        break
    
    if db.get_user_by_username(username):
        print(f"❌ Username '{username}' already exists.")
        return
    
    if db.get_user_by_email(email):
        print(f"❌ Email '{email}' already exists.")
        return
    
    try:
        user_dict = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "password_hash": db.hash_password(password),
            "role": role,
            "is_active": True,
            "email_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "permissions": ["manage_documents", "view_analytics"] if role == "user" else ["admin", "manage_users", "manage_documents", "view_analytics"]
        }

        result = db.db.users.insert_one(user_dict)
        user_id = str(result.inserted_id)
        
        print(f"✅ {role.capitalize()} account created successfully!")
        print(f"👤 Username: {username}")
        print(f"📧 Email: {email}")
        print(f"🆔 User ID: {user_id}")
        print(f"🎯 Role: {role.capitalize()}")
        
    except Exception as e:
        print(f"❌ Error creating account: {e}")


def list_users():
    """Display all users in the database."""
    users = db.db.users.find()
    users_list = list(users)  
    if not users_list:  
        print("❌ No users found.")
        return
    
    print("\nUser List:")
    for user in users_list:
        print(f"👤 Username: {user['username']}, Email: {user['email']}, Role: {user['role']}")

def delete_user():
    """Remove a user by username or email."""
    identifier = input("Enter username or email of the user to delete: ").strip()
    result = db.db.users.delete_one({"$or": [{"username": identifier}, {"email": identifier}]})
    
    if result.deleted_count > 0:
        print("✅ User deleted successfully!")
    else:
        print("❌ User not found.")


def main_menu():
    """Main menu for user interactions."""
    while True:
        print("\n1. Create Admin Account")
        print("2. Create User Account")
        print("3. List All Users")
        print("4. Delete User")
        print("5. Exit")
        
        choice = input("Select an option: ")
        
        if choice == "1":
            create_user("admin")
        elif choice == "2":
            create_user("user")
        elif choice == "3":
            list_users()
        elif choice == "4":
            delete_user()
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("❌ Invalid option. Please try again.")


if __name__ == "__main__":
    main_menu()
