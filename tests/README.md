# Harvesting.Food API Testing

The harvesting.food API uses `pytest` and `pytest-cov` for testing and coverage needs and use a
SQLite database.

## Usage

To run the test using `uv`:

```shell
uv run pytest -s -v
```

or to run with a coverage report:

```shell
uv run pytest -s -v --cov=app tests
```


## Naming Convention

Test names should follow the naming convention test_[FUNCTION NAME] or test_[FUNCTION NAME]_[VARIATION],
for example for a route for a function named `my_route_function`:

```python
async def test_my_route_function():
    """"""
```
and/or

```python
async def test_my_route_function_with_extra():
    """"""
```
