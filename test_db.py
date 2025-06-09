from app import create_app
from app.models.user import User, db

def test_database():
    # Create the application context
    app = create_app()
    
    with app.app_context():
        # Create a test user
        test_user = User(
            username='testuser',
            email='test@example.com'
        )
        test_user.set_password('testpassword123')
        
        # Add the user to the database
        db.session.add(test_user)
        db.session.commit()
        
        # Query the user
        user = User.query.filter_by(username='testuser').first()
        if user:
            print(f"User found: {user.username}")
            print(f"Email: {user.email}")
            print("Password verification test:", user.check_password('testpassword123'))
        
        # List all users
        print("\nAll users in database:")
        users = User.query.all()
        for user in users:
            print(f"- {user.username} ({user.email})")

if __name__ == '__main__':
    test_database() 