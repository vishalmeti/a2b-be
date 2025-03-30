# Borrow Anything (Hyperlocal Backend) 🤝

This repository contains the backend API server for the **Borrow Anything** application, built with Django and Django REST Framework.

*(README generated: Sunday, March 30, 2025 at 4:40 AM IST, Bengaluru, Karnataka, India)*

## The Problem 🤔

In dense urban environments like Bengaluru, people often need everyday items temporarily (e.g., a specific kitchen utensil, extra chairs for a party, a travel bag for a short trip) but don't want to buy them for infrequent use. This leads to wasted money, resources, and storage space. While asking friends is possible, it's often inconvenient or relies on knowing who has what.

## The Solution: Hyperlocal Sharing ✨

**Borrow Anything** aims to create a trusted micro-sharing economy within specific, small geographical areas like apartment complexes or residential layouts. By leveraging the inherent trust and convenience of proximity, the platform connects neighbors to facilitate the borrowing and lending of everyday non-tool items.

This backend provides the API infrastructure to support the mobile application (built separately, likely in React Native).

## Core Features Implemented ✅

* **User Management:** Registration, JWT Login (Access/Refresh Tokens), Profile view/update (`/me`).
* **Community System:** Listing approved communities (filtered by pincode/city), User suggestions for new communities, Admin approval workflow (via Django Admin), Assigning users to communities via profile update.
* **Item Management:** Category listing, Full CRUD for Items (Create, Read, Update, Delete) scoped to the user's community, Owner-only permissions for modification.
* **Image Handling:** Separate endpoint for image uploads (manual S3 storage using user-provided keys), pre-signed URL generation for image retrieval.
* **Borrowing Workflow:** Full request lifecycle (Create, Accept, Decline, Cancel, Confirm Pickup, Confirm Return, Complete). Item availability status updates. Auto-rejection of conflicting requests.

## Technology Stack 🔧

* **Backend Framework:** Django (~5.x)
* **API Framework:** Django REST Framework (DRF)
* **Database:** PostgreSQL
* **Database Adapter:** Psycopg2
* **Authentication:** JWT via `djangorestframework-simplejwt`
* **Image Storage:** AWS S3 (using `boto3` for direct interaction)
* **Environment Variables:** `python-dotenv`
* **Filtering:** `django-filter`
* **Language:** Python (3.10+)
* **(Frontend:** To be built separately, e.g., using React Native)

## Project Status 📊

* [ ] Planning
* [x] **In Development** (Core features implemented)
* [ ] Alpha/Beta Testing
* [ ] Production

*(Mark the current status)*

## Getting Started 🚀

### Prerequisites

* Python (3.10 or higher recommended) & Pip
* PostgreSQL Server (running locally or accessible via network/Docker)
* Git
* AWS Account & S3 Bucket configured with IAM User Credentials (Access Key ID, Secret Access Key)

### Installation & Setup

1.  **Clone:** `git clone <your-repository-url>` and `cd borrow_anything_project`
2.  **Virtual Env:** `python -m venv venv` then activate (`source venv/bin/activate` or `.\venv\Scripts\activate`)
3.  **Install Deps:** `pip install -r requirements.txt` *(Ensure `requirements.txt` includes `django`, `djangorestframework`, `psycopg2-binary`, `djangorestframework-simplejwt`, `python-dotenv`, `boto3`, `django-filter`, `Pillow`)*
4.  **Setup PostgreSQL:** Create a database and user (e.g., `borrowdb`, `borrowuser`).
5.  **Configure Environment:**
    * Copy the example environment file: `cp .env.example .env`
    * **Edit the `.env` file** with your actual settings: `SECRET_KEY`, DB credentials, **AWS credentials (Key ID, Secret Key)**, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_PRESIGNED_URL_EXPIRATION`, etc. *(Refer to the `.env.example` file)*
6.  **Apply Migrations:** `python manage.py migrate`
7.  **Create Superuser:** `python manage.py createsuperuser`

## Running the Application ▶️

```bash
python manage.py runserver
