# Aras Quick Reference

## Environment Variables (`.env`)
- `FLASK_APP`
- `FLASK_ENV` (development, testing, production)
- `SQLALCHEMY_DATABASE_URI`
- `SECRET_KEY`

## Aras CLI Commands
`flask aras dbtest`     # Test database connection
`flask aras dbinit`     # Initialize database structure
`flask aras dbca`       # Create all tables based on models
`flask aras filldata`   # Seed database with test data
`flask aras csu`        # Create superuser account
`flask aras reset`      # Reset user password

## Testing & Formatting
`pytest tests/`                   # Run entire test suite
`pytest tests/test_file.py::test_name` # Run specific test
`black aras/ arasCore/`           # Format code
`isort aras/ arasCore/`           # Sort imports