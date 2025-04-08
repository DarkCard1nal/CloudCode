#!/bin/bash

# Check for arguments
if [ "$#" -eq 0 ]; then
  # Run all tests if no arguments provided
  docker-compose --profile testing run tests
elif [ "$1" = "unit" ]; then
  # Run unit tests
  docker-compose --profile testing run tests python Tests/unit/run_unit_tests.py
elif [ "$1" = "integration" ]; then
  # Run all integration tests excluding Behave feature tests
  docker-compose --profile testing run tests python -m unittest discover -s Tests/integration
else
  # Run selected tests if arguments are provided
  docker-compose --profile testing run tests python -m behave "$@"
fi 