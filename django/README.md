# Dockerized_Django

### Why?

Containerized Django is hard, frusterating, and makes you want to just go the easy route and start a VM.  If you're running docker, or even researching containerization, you're probably already starting to understand the benefits of containerization.  This project was born out of curiosity for me, to see if I could successfully create a single stack that could successfully host a django project from both development and production environments. 

This stack utilizes a postgres backend and an nginx front end by utilizing the proxy_pass function.  

### How does it work?  

Initially, when we create a docker stack, we either use `docker compose run` or more likely use a docker compose script that defines everything we need.  Using a docker compose script makes things more clean, readable, and in my opinion easier to bring up a stack. The thing is though, this is just one of many layers.  Many "magic" things happen behind the scenes.  Personally, for a long time I always just ignored it and took advantage of the fact that a lot of times things "just worked" and didn't bother understanding how or why it worked.

In the docker compose you can see that the three containers that make up this stack are all tied to eachother.  The Postgres DB comes up first.  Django waits on it to start up before it starts, and nginx waits on Django to finish starting up before it starts.  Django and nginx are essentially networked together with postgres.  Postgres has it own volume where the database is stored.  This way, the data persists on the database after your stack is brought down and back up for whatever reason.

When you run docker compose, it can also execute something called a `Dockerfile`.  This is the meat and potatoes of this project.  `Dockerfile` essentially takes the project that you developed on your machine, and copies it into the container.  If you look inside `docker-compose.yaml` you can see that the django container points to the `Dockerfile` contained in this repo.  If you open up that `Dockerfile` you can see a list of sequentially executed commands that occur once, when the container image is built.  After container creation you'll see that the local django project would have been copied into the container, and that is how the container is able to serve up the django project you've been working on.

When running a django container there is some mystery in it as to how it knows what to do with the environment variables you give it.  This is where the `entrypoint.sh` comes in.  The `entrypoint.sh` is essentially a set instructions given to the OS to execute when it's brought up.  

A production django server cannot be complete without a frontend compliment, which is where nginx comes through.  Nginx passes data back and fourth from port 8000 to 8001 (if you leave it set that way) using a software proxy function called `proxy_pass` and you can then pass your reverse proxy over it to complete the system.
