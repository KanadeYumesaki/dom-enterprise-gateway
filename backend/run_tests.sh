#!/bin/bash
poetry run pytest app/tests/test_auth_service.py -vv > pytest_full.log 2>&1
