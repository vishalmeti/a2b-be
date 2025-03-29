# Borrow Anything (Hyperlocal Backend)

This repository contains the backend API server for the "Borrow Anything" application, built with Django and Django REST Framework.

## The Problem

In dense urban environments like Bengaluru, people often need everyday items temporarily (e.g., a specific kitchen utensil, extra chairs for a party, a travel bag for a short trip) but don't want to buy them for infrequent use. This leads to wasted money, resources, and storage space. While asking friends is possible, it's often inconvenient or relies on knowing who has what.

## The Solution: Hyperlocal Sharing

"Borrow Anything" aims to create a trusted micro-sharing economy within specific, small geographical areas like apartment complexes or residential layouts. By leveraging the inherent trust and convenience of proximity, the platform connects neighbors to facilitate the borrowing and lending of everyday non-tool items.

This backend provides the API infrastructure to support the mobile application (built separately, likely in React Native).

## Core Features

* **Hyperlocal Focus:** Users operate within verified communities (e.g., apartment complexes).
* **Item Listing:** Users can easily list items they're willing to lend (photos, description, terms).
* **Item Browse & Searching:** Users can browse/search items available *only* within their community.
* **Borrowing Requests:** Simple request workflow (request -> accept/decline -> coordinate).
* **In-App Chat:** Facilitates coordination between lender and borrower for pickup/return.
* **User Profiles & Reputation:** Ratings and reviews build trust within the community.
* **Community Management:** System for suggesting and approving new communities.
* **Notifications:** Keep users updated on requests, messages, and reviews.

## Technology Stack

* **Backend Framework:** Django (~5.x)
* **API Framework:** Django REST Framework (DRF)
* **Database:** PostgreSQL
* **Database Adapter:** Psycopg2
* **Authentication:** Token Authentication (DRF Authtoken)
* **Environment Variables:** python-dotenv
* **Language:** Python (3.10+)
* **(Frontend:** To be built separately, e.g., using React Native)

## Project Status

* [ ] Planning
* [x] **In Development**
* [ ] Alpha/Beta Testing
* [ ] Production

*(Mark the current status)*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* **Python** (3.10 or higher recommended) & **Pip**
* **PostgreSQL** Server (running locally or accessible via network/Docker)
* **Git**

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd borrow_anything_project
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    *(Ensure you have created a `requirements.txt` file first: `pip freeze > requirements.txt`)*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up PostgreSQL Database:**
    * Ensure your PostgreSQL server is running.
    * Create a dedicated database and user for this project (see example `psql` commands below or use a GUI tool):
        ```sql
        -- Run these in psql as the postgres user
        CREATE DATABASE borrowdb;
        CREATE USER borrowuser WITH PASSWORD 'yoursecurepassword'; -- Use a strong password!
        ALTER ROLE borrowuser SET client_encoding TO 'utf8';
        ALTER ROLE borrowuser SET default_transaction_isolation TO 'read committed';
        ALTER ROLE borrowuser SET timezone TO 'UTC';
        GRANT ALL PRIVILEGES ON DATABASE borrowdb TO borrowuser;
        ```

5.  **Configure Environment Variables:**
    * Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    * **Edit the `.env` file** with your actual settings:
        * `SECRET_KEY`: Generate a new strong secret key (you can use an online generator or Django's `get_random_secret_key()` function via `manage.py shell`).
        * `DEBUG`: Set to `True` for development.
        * Database variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) should match the database you set up in the previous step.
        * *(Add any other necessary environment variables here as the project grows, e.g., email settings, cloud storage keys)*

6.  **Apply Database Migrations:**
    * This creates the necessary tables in your PostgreSQL database based on the Django models.
    ```bash
    python manage.py migrate
    ```

7.  **Create a Superuser (Admin):**
    * This account allows you to access the Django Admin interface.
    ```bash
    python manage.py createsuperuser
    ```
    * Follow the prompts to set a username, email, and password.

## Running the Application

1.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```
2.  The API should now be accessible at `http://127.0.0.1:8000/` (or the port specified).
3.  Access the Django Admin interface at `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.

## API

* The base URL for the API is `/api/v1/`.
* Authentication is handled via **Token Authentication**. Clients must include the header `Authorization: Token <user_token>` on protected endpoints.
* Obtain a token by POSTing `{ "username": "your_user", "password": "your_password" }` to `/api/v1/auth/token/`.
* **(Optional):** Link to more detailed API documentation (e.g., Swagger/OpenAPI documentation generated later).

## Running Tests

*(Add instructions here once tests are implemented)*
```bash
# Example:
# python manage.py test apps.items
# python manage.py test # To run all tests
