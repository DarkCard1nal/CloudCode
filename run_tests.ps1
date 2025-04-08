# PowerShell script for running tests in Docker

# Check for arguments
if ($args.Count -eq 0) {
    # Run all tests if no arguments provided
    docker-compose --profile testing run tests
}
elseif ($args[0] -eq "unit") {
    # Run unit tests
    docker-compose --profile testing run tests python Tests/unit/run_unit_tests.py
}
elseif ($args[0] -eq "integration") {
    # Run all integration tests excluding Behave feature tests
    docker-compose --profile testing run tests python -m unittest discover -s Tests/integration
}
else {
    # Collect all arguments into a single string
    $testArgs = $args -join " "
    # Run selected tests if arguments are provided
    docker-compose --profile testing run tests python -m behave $testArgs
} 