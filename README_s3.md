# S3 File Manager

A web-based application for secure S3 file management that allows authenticated users to upload and download files to/from AWS S3 buckets through an intuitive web interface.

## Features

- **User Authentication**: Secure login with username/password mapped to AWS credentials
- **S3 Bucket Navigation**: Browse buckets and folders with intuitive navigation
- **Multiple File Upload**: Upload multiple files simultaneously with progress tracking
- **Multiple File Download**: Download multiple files with progress tracking
- **AWS China Support**: Configured for AWS China (cn-north-1) region
- **Responsive Web Interface**: Modern, responsive design that works across browsers

## Prerequisites

- Python 3.8 or higher
- AWS Account with S3 access in China region (cn-north-1)
- EC2 instance (for deployment)

## Installation

1. Clone or download the project files to your EC2 instance

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create environment configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Configure user credentials:
   ```bash
   # Edit config/users.json with your AWS credentials
   nano config/users.json
   ```

## Configuration

### Environment Variables (.env)

```bash
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=production
FLASK_PORT=8080
AWS_REGION=cn-north-1
```

### User Credentials (config/users.json)

```json
{
  "users": {
    "your_username": {
      "password": "your_password",
      "aws_credentials": {
        "access_key": "YOUR_AWS_ACCESS_KEY",
        "secret_key": "YOUR_AWS_SECRET_KEY",
        "region": "cn-north-1"
      }
    }
  }
}
```

## Running the Application

### Development Mode
```bash
python app.py
```

### Production Mode (EC2)
```bash
# Set environment to production
export FLASK_ENV=production

# Run the application
python app.py
```

The application will be available at `http://your-ec2-ip:8080`

## Security Considerations

1. **Change the SECRET_KEY**: Use a strong, random secret key in production
2. **Secure Credentials**: Store AWS credentials securely and never commit them to version control
3. **EC2 Security Group**: Ensure port 8080 is only accessible from trusted IP ranges
4. **HTTPS**: Consider using a reverse proxy (nginx) with SSL certificates for production

## Project Structure

```
s3-file-manager/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration template
├── README.md             # This file
├── auth/                 # Authentication module
├── s3_operations/        # S3 operations module
├── file_operations/      # File upload/download operations
├── config/               # Configuration files
│   └── users.json       # User credentials (configure this)
├── templates/            # HTML templates
│   └── base.html        # Base template
└── static/              # Static files (CSS, JS)
    ├── css/
    └── js/
```

## API Endpoints

- `GET /` - Login page
- `POST /login` - Authentication
- `GET /dashboard` - Main file browser
- `GET /api/buckets` - List S3 buckets
- `GET /api/objects` - List objects in bucket/folder
- `POST /api/upload` - Upload files
- `POST /api/download` - Download files
- `GET /health` - Health check

## Development Status

This is the initial project structure. Additional features will be implemented in subsequent tasks:

- [ ] Authentication system
- [ ] S3 integration
- [ ] File upload/download
- [ ] Progress tracking
- [ ] Error handling
- [ ] Testing

## License

This project is for internal use. Please ensure compliance with your organization's security policies.