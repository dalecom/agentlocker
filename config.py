import os

# Get full paths
instance_dir = os.path.join(os.getcwd(), 'instance')
db_file = os.path.join(instance_dir, 'ai_directory.db')

print("Database file path:", db_file)
print("Database file exists:", os.path.exists(db_file))

# List all files in instance directory
print("\nFiles in instance directory:")
for file in os.listdir(instance_dir):
    print(f"- {file}")

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_file}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'team@agentlocker.ai'
    MAIL_PASSWORD = 'kizzqdaydmuxdnsw'
    MAIL_DEFAULT_SENDER = 'team@agentlocker.ai'
