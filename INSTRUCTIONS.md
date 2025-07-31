## Instructions
The steps listed below in Local Development can all be done as-is after cloning this repository and you will be greeted with a very basic `Hello world!" html response. It is not required but we all like to make sure things work before we do work, right?

### Local Development:
* `python -m venv env`
* `source env/bin/activate`
* `pip install --upgrade pip`
* `pip install -r django/requirements.txt`
* Edit the `.env.example` file and replace all the fields as appropriate
* Save as `.env`
* `python django/manage.py migrate`
* `python django/manage.py createsuperuser`
* `python django/manage.py runserver 8001 --settings=project.settings.development`
* Visit http://0.0.0.0:8001/ in your browser to verify its running

Following this, must first develop your project locally as you normally would.  Use this file structure as a base.  Feel free to do the standard things expected and get your project in a state which you're ready to test and troubleshoot it in a containerized state.  This project comes with the base django project and an initial app to get you started.  Adding further apps is all still very standard.  

This package comes with a few other things I like to use in Django projects like `gunicorn`, `python-decouple`, `django-debug-toolbar` & `django-jazzmin`. Feel free to add to the package requirements, just don't foret to update the requirements.txt.  

If you need to add environment variables, add to the `.env` file and retrieve any variables using `python-decouple` or other means.  This will still use `sqlite3` as a development database which will be cleaned up later with provided scripts.  

From here forward we will be working more closely with environment variables.  To name some key ones we use during development - `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_USERNAME` & `DJANGO_SUPERUSER_PASSWORD`.

### Containerized Development:

NOTE(s) on when developing in the containerized state:
a. the project will continue to use the sqlite3 database server.  If you need to wipe the database, you need only restart the continer
b. any changes made to code will not be reflected to the container state until the container is removed and rebuilt via docker-compose

* Edit the `docker-compose.yaml` if you chose to define the project name, and apply the project name there as well as the container names.  Leave the `project` folder name as is.  There will be instructions on how to modify that later.
* Save it as is.
* `docker build --no-cache -t d-django:latest --file ./django/Dockerfile.django ./django/`
* `docker build --no-cache -t d-nginx:latest --file ./nginx/Dockerfile.nginx ./nginx/`
* `docker compose --file=docker-compose.yaml up --detach`
* Visit http://0.0.0.0:8001/ in your browser to verify its running

### Deployment:
You should run the `reset_prod_project.sh` script before building a production stack.

### Production (WIP):

NOTE(s) on when developing in the containerized state:
a. the project will start to use the postgres server if you leave it set to do so.  The postgres server is set up to persist on restarting the stack, but it will _not_ persist if you rebuild the stack.  If you need to wipe the database, you should rebuild the stack.  If you need to update your project, you should also rebuild the stack but preserve your database volume.  In production, it is usually recommended to have a separate external database server.  If you choose that route, you need only change the production.py settings and use the `docker-compose-nopostgres.yaml` when (re)building your stack.

### Rebuilding the Stack (from the root of the cloned repository)
```
docker compose down --volumes --rmi all
docker build --no-cache -t d-django:latest --file  /django/Dockerfile.django ./django/
docker build --no-cache -t d-nginx:latest --file ./nginx/Dockerfile.nginx ./nginx/
docker compose --file=docker-compose.yaml up --detach
```