# Unit/E2E Tests

This folder contains pretty much all the unit and E2E tests for Jars.

```bash
# install test dependencies
pip install pytest pytest-asyncio aiosqlite httpx

# run all tests
pytest tests/ -v

# or run with coverage
pytest tests/ -v --cov=application --cov-report=html

# run specific test file
pytest tests/test_auth.py -v

# if you would like to run specific test class
pytest tests/test_auth.py::TestUserRegistration -v

# or just run a specific test
pytest tests/test_auth.py::TestUserRegistration::test_register_free_user_success -v
```