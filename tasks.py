import os

from invoke import task


@task
def reformat(c):
    c.run("isort mopidy_advanced_scrobbler tests setup.py tasks.py")
    c.run("black mopidy_advanced_scrobbler tests setup.py tasks.py")


@task
def lint(c):
    c.run("flake8 --show-source --statistics --max-line-length 100 mopidy_advanced_scrobbler tests")
    c.run("check-manifest")


@task
def test(c):
    args = ["pytest", "--cov=mopidy_advanced_scrobbler", "--cov-branch", "--cov-report=term"]
    if os.environ.get("CI", "false") == "true":
        args.append("--cov-report=xml")
    else:
        args.append("--cov-report=html")

    c.run(" ".join(args))


@task
def type_check(c):
    c.run("mypy mopidy_advanced_scrobbler tests")
