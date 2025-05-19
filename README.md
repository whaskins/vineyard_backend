# Vineyard Inventory Management System

A complete solution for vineyard inventory management with a FastAPI backend and Angular dashboard.

## Technology Stack

- **Backend (FastAPI)**: Modern, fast API framework with async support
- **Database (PostgreSQL)**: Relational database for data storage
- **Dashboard (Angular)**: Responsive web interface for inventory management
- **Docker**: Containerization for easy deployment and scaling

## System Architecture

The system consists of three main components:

1. **Backend API (FastAPI)**: Handles all business logic, data processing, and database operations
2. **Database (PostgreSQL)**: Stores all vineyard inventory data
3. **Web Dashboard (Angular)**: Provides a user-friendly interface for viewing and managing inventory

## Features

- **Vine Management**: Add, update, search, and delete vine records
- **Maintenance Tracking**: Record and manage maintenance activities
- **Issue Reporting**: Report and track vineyard issues with photos
- **Authentication**: Secure API and dashboard with JWT authentication
- **Bulk Editing**: Modify multiple vine records simultaneously
- **Data Visualization**: View key statistics and reports
- **Responsive Design**: Works on desktop and mobile devices

## Running the System with Docker

### Prerequisites

- Docker and Docker Compose
- AWS CLI configured (for pulling images from ECR)

### Step 1: Authentication with ECR

Authenticate Docker with AWS ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 283282846400.dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Environment Configuration

Create an `.env` file in the same directory as the `docker-compose.yml` file with the following variables:

```
# Database settings
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=vineyard_inventory

# JWT token settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Superuser settings for first run
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin
```

### Step 3: Start the System

Run the following command in the directory containing `docker-compose.yml`:

```bash
docker-compose up -d
```

This will start all three components:
- The web dashboard will be available at http://localhost
- The backend API will be available at http://localhost:8080
- The PostgreSQL database will be running internally

### Step 4: Access the Dashboard

Open your web browser and navigate to:

```
http://localhost
```

You can log in with the default superuser credentials defined in your `.env` file.

## API Endpoints

The API is organized around the following resources:

### Authentication

- `POST /api/v1/login/access-token` - Obtain JWT token
- `POST /api/v1/login/test-token` - Test authentication token
- `POST /api/v1/login/password-recovery/{email}` - Recover password

### Users

- `GET /api/v1/users/` - List all users (admin only)
- `POST /api/v1/users/` - Create a new user (admin only)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user (admin only)

### Vines

- `GET /api/v1/vines/` - List all vines
- `POST /api/v1/vines/search` - Search vines with filters and pagination
- `POST /api/v1/vines/` - Create a new vine
- `PUT /api/v1/vines/sync` - Create or update a vine (for mobile syncing)
- `GET /api/v1/vines/{vine_id}` - Get vine by ID
- `GET /api/v1/vines/by-alpha-id/{alpha_id}` - Get vine by alphanumeric ID
- `GET /api/v1/vines/by-location/{field_name}/{row_number}/{spot_number}` - Get vines by location
- `PUT /api/v1/vines/{vine_id}` - Update a vine
- `DELETE /api/v1/vines/{vine_id}` - Delete a vine (admin only)

### Maintenance

- `GET /api/v1/maintenance/types` - List all maintenance types
- `POST /api/v1/maintenance/types` - Create a new maintenance type
- `GET /api/v1/maintenance/types/{type_id}` - Get maintenance type by ID
- `PUT /api/v1/maintenance/types/{type_id}` - Update a maintenance type
- `DELETE /api/v1/maintenance/types/{type_id}` - Delete a maintenance type (admin only)
- `GET /api/v1/maintenance/activities` - List all maintenance activities
- `POST /api/v1/maintenance/activities` - Create a new maintenance activity
- `GET /api/v1/maintenance/activities/{activity_id}` - Get maintenance activity by ID
- `GET /api/v1/maintenance/activities/vine/{vine_id}` - Get maintenance activities for a vine
- `PUT /api/v1/maintenance/activities/{activity_id}` - Update a maintenance activity
- `DELETE /api/v1/maintenance/activities/{activity_id}` - Delete a maintenance activity

### Issues

- `GET /api/v1/issues/` - List all issues
- `GET /api/v1/issues/with-details` - List all issues with detailed information
- `POST /api/v1/issues/` - Create a new issue
- `GET /api/v1/issues/{issue_id}` - Get issue by ID
- `GET /api/v1/issues/{issue_id}/with-details` - Get issue with detailed information
- `GET /api/v1/issues/vine/{vine_id}` - Get issues for a vine
- `GET /api/v1/issues/status/{is_resolved}` - Get issues by resolution status
- `PUT /api/v1/issues/{issue_id}` - Update an issue
- `DELETE /api/v1/issues/{issue_id}` - Delete an issue

## Troubleshooting

If you encounter any issues:

1. Check the logs:
   ```bash
   docker-compose logs
   ```

2. For specific service logs:
   ```bash
   docker-compose logs api
   docker-compose logs dashboard
   docker-compose logs db
   ```

3. To restart a specific service:
   ```bash
   docker-compose restart api
   ```

4. To rebuild and restart all services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Mobile App Integration

This system integrates with the Flutter mobile app:

- The backend API supports mobile app synchronization
- The web dashboard complements the mobile app for admin and management tasks
- Both use the same authentication system and data models

## License

This project is licensed under the MIT License.# vineyard_backend
