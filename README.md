# OnlineBookstore

## Overview

This is a bookstore website focusing on backend using Django and mysql. The frontend does not have a framework, so the
looks is plain.

This website has canonical features of an online bookstore such as book recommendation, book search, rating books, making
comments, rating comments, adding to shopping cart, making orders. Customers can also trust/untrust other customers, and ask questions to the managers.

In addition, managers have the features of adding new book, managing stock and price, generating report on popular
books/authors/publishers, generating report on trustworthiness/usefulness of customers

## Running the website with Django's development server locally

### Prerequisite

- Install mysql-server for your system and start the service
- Create a database \<my_db> with credentials \<my_user> and \<my_password> and grant all privileges to \<my_user>
- python 3.8
- pip

### Then

1. Clone this repository
2. `cd OnlineBookstore`
3. `pip install -r requirements.txt` (preferably in a python virtual environment)
4. Find DATABASES in `./OnlineBookstore/settings.py` and replace NAME with \<my_db>, USER with \<my_user>, PASSWORD with
  \<my_password>
5. `python3 manage.py createsuperuser` and answer prompt to let Django create a superuser (manager)
6. `python3 manage.py migrate` to let Django create needed tables in the database
7. `python3 manage.py runserver` to start the Django development server and follow the URL in the console to see the
  website (default url on Linux is http://127.0.0.1:8000/)
8. Visit http://127.0.0.1:8000/admin and login using credentials entered in step 5 to see most manager features
9. Visit http://127.0.0.1:8000/home/admin_book_report and http://127.0.0.1:8000/home/admin_book_report to see manager book report and user report
