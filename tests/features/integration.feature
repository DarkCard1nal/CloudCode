Feature: CloudCode Integration Tests
	As a user of CloudCode
	I want to ensure client and server work together seamlessly
	So that I can process tasks efficiently and securely

	Background:
		Given the server is running with security checker enabled
		And the client is connected to the server

	Scenario: Client reconnection after server restart
		Given the server is running for testing
		And the client is connected
		When the server is restarted
		Then the client should detect the disconnection
		And automatically reconnect when the server is available
		And continue processing tasks without manual intervention 