# Aurora

Aurora is an open source project to collect and register data.
It is focused mainly on performance and security.


### Run the code 

- Option 1: with local machine services (redis, postgres) with `direnv`

First configure your `.envrc` and run

```shell
  python manage.py runserver
````

- Option 2: using docker compose

For the first time you need to run in root project directory

```shell
./manage env --comment --defaults > .env
docker compose build
docker compose up
```

each next time

```shell
docker compose up
```
