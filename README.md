                  # CeroPJ
A Django web application for CeroPJ with public artist, event, and studio pages, a booking workflow, and an editor-friendly Django admin.
## Features
- Public pages for home, about, contact, artists, events, studio, and bookings
- Artist profiles and event listings
- Upcoming and past events
- Event calendar and `.ics` export
- Search, filtering, and pagination for artist and event listings
- Booking / enquiry workflow
- Internal notification emails and requester confirmation emails
- Booking reference numbers
- Honeypot anti-spam protection on booking forms
- Custom error pages
- Sitemap and robots support
- Django admin for content management
- Demo seed command for local development
## Tech Stack
- Python
- Django 6
- PostgreSQL
- WhiteNoise for production static files
- Local filesystem media storage
- Django admin
## Project Structure
- `apps/core` – shared utilities, admin helpers, and management commands
- `apps/pages` – site settings and editable page sections
- `apps/artists` – artist profiles and artist pages
- `apps/events` – event listings, categories, calendar feed, and `.ics` export
- `apps/studio` – studio service listings
- `apps/bookings` – booking and enquiry workflow
- `config/settings` – base, development, and production settings
- `templates` – public-facing templates
- `static` – CSS, JavaScript, and static assets
- `media` – uploaded files in development
## Requirements
Make sure you have these installed locally:
- Python 3.11+
- PostgreSQL
- pip
- virtualenv support (`python -m venv`)
## Local Setup
### 1. Clone the project
```bash
git clone https://github.com/joaquinantonio/ProjectCero
cd ProjectCero
```
### 2. Create and activate a virtual environment
macOS / Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```
Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
### 3. Install dependencies
The repository currently does not include a checked-in requirements file, so install the core packages manually:
```bash
pip install django psycopg[binary] pillow python-decouple whitenoise icalendar
```
### 4. Create your environment file
Copy the example values below into `.env` and adjust them for your machine:
```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=
DB_NAME=cerodb
DB_USER=cero_admin
DB_PASSWORD=change-me
DB_HOST=127.0.0.1
DB_PORT=5432
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=CeroPJ <no-reply@example.com>
BOOKING_NOTIFICATION_EMAIL=notify@example.com
```
### 5. Settings modules
Development uses `config.settings.dev`.
Production uses `config.settings.prod`.
If you need to set the environment variable manually:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.dev
```
Windows:
```bash
set DJANGO_SETTINGS_MODULE=config.settings.dev
```
## Database Setup
Create a PostgreSQL database and user for the project.
Example:
```sql
CREATE DATABASE cerodb;
CREATE USER cero_admin WITH PASSWORD 'change-me';
ALTER DATABASE cerodb OWNER TO cero_admin;
```
> Use a dedicated PostgreSQL user for the project instead of the default `postgres` superuser.
## Database Migrations
Run migrations after configuring your environment:
```bash
python manage.py makemigrations
python manage.py migrate
```
If you want to inspect generated SQL for a migration:
```bash
python manage.py sqlmigrate app_name migration_number
```
## Create an Admin User
Create a Django superuser:
```bash
python manage.py createsuperuser
```
Admin is available at:
```text
/admin/
```
If you need to reset a password:
```bash
python manage.py changepassword your_admin_username
```
## Seed Demo Data
To load demo content into the database:
```bash
python manage.py seed_demo_data
```
To reset and reseed demo content:
```bash
python manage.py seed_demo_data --reset
```
This seeds:
- site settings
- page sections
- event categories
- featured artists
- events and event relationships
- studio service categories and services
- sample booking requests
## Run the Development Server
```bash
python manage.py runserver
```
Then open:
- Home: `/`
- About: `/about/`
- Contact: `/contact/`
- Artists: `/artists/`
- Events: `/events/`
- Calendar: `/events/calendar/`
- Studio: `/studio/`
- Bookings: `/bookings/`
- Admin: `/admin/`
## Email Testing
### Local testing
Use Django’s console backend in `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```
Then submit a booking form. Emails print to the terminal running `runserver`.
### File-based testing
You can also use the file backend for development:
```env
EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
```
## Booking Email Behavior
For successful booking requests, the app:
- sends an internal notification email
- sends a confirmation email to the requester
- stores a booking reference number
## Anti-Spam
Booking forms use a basic honeypot field.
This means:
- normal users do not see it
- bots often fill it
- filled honeypot submissions are blocked
## Running Tests
Run all tests:
```bash
python manage.py test
```
Tests cover areas such as:
- booking submission
- booking anti-spam
- booking email flow
- public event visibility
- artist pages
- search and filtering behavior
## Admin Notes
The admin is designed to be editor-friendly.
It currently includes:
- image previews
- inline event-artist management
- bulk actions for booking statuses
- event publish / feature actions
- editable ordering / activation in list views where safe
## Public Web / SEO Features
The app includes:
- custom error pages
- `sitemap.xml`
- `robots.txt`
- page-specific metadata blocks for title, description, and Open Graph previews
## Static and Media Files
### Static files
Static files include CSS, JavaScript, and bundled static images.
In production, Django collects them into `STATIC_ROOT` using:
```bash
python manage.py collectstatic --settings=config.settings.prod
```
### Media files
Media files include uploads such as artist images, event posters, and studio service images.
In development, media is stored on the local filesystem.
## Production Settings
Production uses:
- `config.settings.prod`
- `DEBUG = False`
- HTTPS / cookie / HSTS security settings
- WhiteNoise for static file serving
- logging and `ADMINS` for error emails
Run deployment checks with:
```bash
python manage.py check --deploy --settings=config.settings.prod
```
## WhiteNoise
WhiteNoise is used for serving **static files** in production.
What Django does with it:
1. `collectstatic` gathers static files into `STATIC_ROOT`
2. WhiteNoise serves those static files in production
3. Django continues handling dynamic pages normally
> WhiteNoise is for static files, not uploaded media files.
## Useful Commands
### Run server
```bash
python manage.py runserver
```
### Make migrations
```bash
python manage.py makemigrations
```
### Apply migrations
```bash
python manage.py migrate
```
### Create superuser
```bash
python manage.py createsuperuser
```
### Seed demo data
```bash
python manage.py seed_demo_data
```
### Reset and reseed demo data
```bash
python manage.py seed_demo_data --reset
```
### Run tests
```bash
python manage.py test
```
### Collect static files for prod
```bash
python manage.py collectstatic --settings=config.settings.prod
```
### Run deployment checks
```bash
python manage.py check --deploy --settings=config.settings.prod
```
