# 🥬🥒🍅 Harvesting.Food API 🥬🥦🥒🥕🫑🌶️

The harvest.food API is a FastAPI backend for a site to create and track your garden. The site is
designed that you can create a garden, add a bed, and add plants. You can track their progress over
time and track your harvest when it all comes to fruition. The site incorporates AI suggestions and
advice for novice gardeners and for experts that might want a little help.

## ⬇️ Installation

Install the site locally by cloning the repo and running `uv sync` to install the dependencies. If
you are not familiar with [uv](https://docs.astral.sh/uv/) follow this link for more information.

You will need to copy the [.env.example](.env.example) file to .env and complete with all of the
required values.

## 🚀 Usage

### 🏃 Running with uv

You can run the site locally by running:

```shell
$ uv run fastapi dev
```
The site will require a database connection. The [config.py](app/utils/config.py) will try to
construct the DB connection string from the values in the .env file, but this only works for a
Postgres async connection. If you want to use some other DB, you will need to change the connection
string values in the config file.

### ⛴️ Running in Docker

There is a [docker-compose.yml](docker-compose.yml) and a [Dockerfile](Dockerfile) included in this
repo which you can use to run the site. This is probably the easiest method:

```shell
$ docker compose up --build
```

## 🔐 Casbin

The site uses [Casbin](https://casbin.org/) for access control. You can read more about that in the
[README](app/casbin/README.md) file.

## 🧪 Testing

We are using [pytest](https://docs.pytest.org/en/stable/) and
[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/index.html) for testing and coverage checks.


## 📌 Requirements

- [uv](https://docs.astral.sh/uv/)
- [Docker](https://docs.docker.com/engine/install/) (recommended)

## 📝 License

[Affero GPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
