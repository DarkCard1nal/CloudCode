Feature: Python Security Checker
	As a developer
	I want to check Python files for security issues
	So that I can ensure only safe code is executed on the server
	
	Background:
		Given the Python Security Checker is initialized

	Scenario: Check a safe Python file
		Given I have a Python file with safe code
		When I check the file for security issues
		Then the file should be considered safe
		And the safe file should contain all the original code

	Scenario: Check an unsafe Python file with system access
		Given I have a Python file with "os" module import
		And the file contains system command execution
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the unsafe imports should be removed
		And the system command execution should be removed
		And a safe version of the file should be created

	Scenario: Check an unsafe Python file with code execution
		Given I have a Python file with "eval" function calls
		And the file contains "exec" function calls
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the eval function calls should be removed
		And the exec function calls should be removed
		And a safe version of the file should be created

	Scenario: Check a file with sensitive data
		Given I have a Python file with hardcoded passwords
		And the file contains API keys
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the hardcoded passwords should be removed
		And the API keys should be removed
		And a safe version of the file should be created

	Scenario: Check a mixed Python file
		Given I have a Python file with both safe and unsafe code
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the safe code should be preserved
		And the unsafe code should be removed
		And a safe version of the file should be created

	Scenario: Check a non-existent file
		Given I have a non-existent file path
		When I try to check the file for security issues
		Then I should get a "file not found" error

	Scenario: Check a file that is not a Python file
		Given I have a text file that is not a Python file
		When I try to check the file for security issues
		Then I should get a "not a Python file" error

	Scenario: Multi-layer unsafe imports detection
		Given I have a Python file with hidden imports
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the hidden imports should be removed
		And a safe version of the file should be created

	Scenario Outline: Check files with various security issues
		Given I have a Python file with <issue_type> issues
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the <issue_type> issues should be removed
		And a safe version of the file should be created

		Examples:
			| issue_type           |
			| subprocess           |
			| socket               |
			| file operations      |
			| network access       |
			| pickle               |
			| input validation     |
			
	Scenario: Check GitHub API key detection
		Given I have a Python file with GitHub API keys
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the GitHub API keys should be removed
		And a safe version of the file should be created

	Scenario: Check AWS credentials detection
		Given I have a Python file with AWS credentials
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the AWS credentials should be removed
		And a safe version of the file should be created
		
	Scenario: Check Stripe API keys detection
		Given I have a Python file with Stripe API keys
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the Stripe API keys should be removed
		And a safe version of the file should be created

	Scenario: Check Slack token detection
		Given I have a Python file with Slack tokens
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the Slack tokens should be removed
		And a safe version of the file should be created

	Scenario: Check insecure cryptographic practices
		Given I have a Python file with insecure cryptographic practices
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the insecure cryptographic practices should be detected
		And a safe version of the file should be created

	Scenario: Check ReDOS vulnerabilities
		Given I have a Python file with ReDOS vulnerability
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the ReDOS vulnerabilities should be detected
		And a safe version of the file should be created

	Scenario: Check template injection vulnerabilities
		Given I have a Python file with template injection vulnerabilities
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the template injection vulnerabilities should be detected
		And a safe version of the file should be created
		
	Scenario: Check SSRF vulnerabilities
		Given I have a Python file with SSRF vulnerabilities
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the SSRF vulnerabilities should be detected
		And a safe version of the file should be created

	Scenario: Check container escape attempts
		Given I have a Python file with container escape attempts
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the container escape attempts should be detected
		And a safe version of the file should be created

	Scenario: Check file that exceeds maximum size
		Given I have a Python file that exceeds maximum size
		When I try to check the file for security issues
		Then I should get a "exceeds maximum allowed size" error
		
	Scenario: Check file with invalid encoding
		Given I have a Python file with invalid UTF-8 encoding
		When I try to check the file for security issues
		Then I should get a "encoding" error

	Scenario: Check safe subprocess calls in Docker mode
		Given the Python Security Checker is initialized in Docker mode
		Given I have a Python file with safe subprocess calls
		When I check the file for security issues
		Then the file should be considered safe
		And the safe subprocess calls should be preserved

	Scenario: Check code with safe patterns similar to unsafe ones
		Given I have a Python file with safe patterns similar to unsafe ones
		When I check the file for security issues
		Then the file should be considered safe
		And the safe patterns should be preserved

	Scenario: Check multi-layer code obfuscation
		Given I have a Python file with multi-layer code obfuscation
		When I check the file for security issues
		Then the file should be marked as unsafe
		And the complex obfuscation techniques should be detected
		And a safe version of the file should be created

	Scenario: Check large file processing time
		Given I have a large Python file
		When I check the file for security issues with time measurement
		Then the processing time should be reasonable
		And a safe version of the file should be created 