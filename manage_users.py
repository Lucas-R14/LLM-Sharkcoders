from app import create_app
from app.models.user import User, db
import getpass

def create_user(username, email, password):
    """Create a new user in the database"""
    app = create_app()
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"Error: Username '{username}' already exists")
            return False
        
        if User.query.filter_by(email=email).first():
            print(f"Error: Email '{email}' already exists")
            return False
        
        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        print(f"User '{username}' created successfully!")
        return True

def delete_user(username):
    """Delete a user from the database"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print(f"User '{username}' deleted successfully!")
            return True
        else:
            print(f"Error: User '{username}' not found")
            return False

def list_users():
    """List all users in the database"""
    app = create_app()
    with app.app_context():
        users = User.query.all()
        if users:
            print("\nUsers in database:")
            print("-" * 50)
            for user in users:
                print(f"Username: {user.username}")
                print(f"Email: {user.email}")
                print("-" * 50)
        else:
            print("No users found in database")

def main():
    while True:
        print("\nUser Management System")
        print("1. Create new user")
        print("2. Delete user")
        print("3. List all users")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            username = input("Enter username: ")
            email = input("Enter email: ")
            password = getpass.getpass("Enter password: ")
            create_user(username, email, password)
        
        elif choice == '2':
            username = input("Enter username to delete: ")
            delete_user(username)
        
        elif choice == '3':
            list_users()
        
        elif choice == '4':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 