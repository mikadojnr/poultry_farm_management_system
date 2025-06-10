# Poultry Farm Management System

A modern, web-based management system for poultry farmers to efficiently track and optimize every aspect of farm operations — from livestock and feed to production, health, and finances.

---

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Screenshots](#screenshots)
- [Installation Guide](#installation-guide)
- [Usage](#usage)
- [Sidebar Toggling](#sidebar-toggling)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **User Authentication:** Secure registration and login for multiple users.
- **Livestock Management:** Add, search, filter, and manage individual birds/flocks with details like breed, age, health, and weight.
- **Feed Management:** Record feed purchases, usage, and monitor stock levels.
- **Production Tracking:** Log daily egg collection, sales, mortality, and calculate production rates.
- **Health Records:** Record treatments, vaccinations, illnesses, and vet notes.
- **Financial Management:** Track expenses, sales, and profitability.
- **Notifications:** Get alerts about low feed, equipment maintenance, budget, and more.
- **Responsive Design:** Fully mobile-compatible and accessible.
- **Interactive Dashboard:** Visualize data with charts and statistics.
- **Sidebar Navigation:** Collapsible sidebar with smooth toggling for a focused workspace.

---

## System Architecture

- **Backend:** Python (Flask), SQLAlchemy, SQLite database.
- **Frontend:** HTML, JavaScript (modular, with ES6 classes), Tailwind CSS, custom CSS, Chart.js for analytics.

### Key Models (see `app.py`):

- `User`: Represents users with secure password storage.
- `Livestock`: Poultry details (breed, age, health, weight, status).
- `FeedRecord`: Feed inventory and purchase log.
- `ProductionRecord`: Daily eggs, sales, revenue, and mortality.
- `HealthRecord`: Treatments and health history.
- `FinancialRecord`: Income and expense tracking.

---

## Screenshots

> _To add screenshots, place images in a `/screenshots` folder and link here._

---

## Installation Guide

### Prerequisites

- Python 3.7+
- [pip](https://pip.pypa.io/en/stable/)
- (Optional) Virtual environment tool: `venv` or `virtualenv`

### 1. Clone the Repository

```sh
git clone https://github.com/mikadojnr/poultry_farm_management_system.git
cd poultry_farm_management_system
```

### 2. Create and Activate a Virtual Environment

```sh
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

> If `requirements.txt` is missing, manually install main dependencies:
```sh
pip install Flask Flask-SQLAlchemy Werkzeug
```

### 4. Initialize the Database

```sh
python
>>> from app import db
>>> db.create_all()
>>> exit()
```

Or, run the provided setup script if available.

### 5. Run the Application

```sh
flask run
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Usage

1. **Register:** Sign up for a new account.
2. **Login:** Access your dashboard.
3. **Add Livestock:** Go to "Livestock" and click "Add Livestock".
4. **Manage Feeds:** Record feed purchases and usage.
5. **Track Production:** Log daily eggs, sales, and view analytics.
6. **Monitor Health:** Enter health events, treatments, and vaccinations.
7. **Financials:** Track expenses, revenues, and view profit stats.
8. **Settings:** Adjust notification and data preferences.

---

## Sidebar Toggling

The sidebar can be toggled (collapsed/expanded) for better focus or screen space.

### Desktop

- **Click the Sidebar Toggle Button** (usually a hamburger icon or arrow).
- **Keyboard Shortcut:** Press `Alt + S` to toggle sidebar collapse/expand.

### Mobile

- **Click the Mobile Menu Button** (hamburger icon at top-left).
- **Keyboard Shortcut:** Press `Alt + M` to open/close the sidebar menu.
- **Overlay:** Clicking the overlay closes the sidebar.

#### Implementation Details

- **JS:** See `static/js/main.js` for the `FarmApp` class:
  - `toggleSidebar()`: Handles desktop sidebar collapse.
  - `toggleMobileMenu()`, `openMobileMenu()`, `closeMobileMenu()`: Handles mobile sidebar.
  - State persists using `localStorage`.
  - Responsive to window resize.

- **CSS:** See `static/css/style.css` for sidebar transitions, width, and collapsing behavior:
  - `.sidebar.collapsed` reduces width and hides text.
  - Smooth transitions for width and opacity.

- **HTML:** Sidebar structure in `templates/base.html` with IDs:
  - `sidebar`, `sidebar-toggle`, `mobile-menu-btn`, `mobile-overlay`.

---

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** HTML5, JavaScript (ES6), Tailwind CSS, Chart.js, FontAwesome
- **Authentication:** Werkzeug Security

---

## Folder Structure

```
poultry_farm_management_system/
├── app.py
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── livestock.html
│   ├── add_livestock.html
│   ├── feed.html
│   ├── production.html
│   └── ...
├── README.md
└── ...
```

---

## Contributing

1. Fork this repository.
2. Create a new branch: `git checkout -b feature/YourFeature`.
3. Make your changes and commit: `git commit -am 'Add new feature'`.
4. Push to your fork: `git push origin feature/YourFeature`.
5. Create a Pull Request.

---

## License

[MIT License](LICENSE)

---

_This project is maintained by [mikadojnr](https://github.com/mikadojnr)._