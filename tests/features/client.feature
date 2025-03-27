Feature: Cloud Code Client
	As a client application
	I want to ensure the client works correctly
	So that it can send tasks to the server properly

	Background:
		Given the server is running for client tests
		And the client is initialized

	Scenario: Client sends sequential tasks
		When I send tasks sequentially
		Then all tasks should be sent successfully
		And I should receive results for each task
		And the tasks should be processed in order

	Scenario: Client sends parallel tasks
		When I send tasks in parallel
		Then all tasks should be sent successfully
		And I should receive results for each task
		And the tasks should be processed concurrently

	Scenario: Client sends infinite task
		When I send an infinite task
		Then the task should be sent successfully
		And I should receive a task ID
		And the task should be running on the server
		
	Scenario: Client sends corrupted file
		When I send a corrupted file
		Then the client should handle the error gracefully
		And I should receive an error message
		
	Scenario: Client handles server unavailability
		Given the server is not responding
		When I try to send a task
		Then the client should report connection issues
		And provide proper error feedback
		
	Scenario: Client sends multiple tasks simultaneously
		When I send "10" tasks simultaneously
		Then all tasks should be sent successfully
		And I should receive results for each task
		And the response time should be within acceptable limits
		
	Scenario: Client handles task timeout
		When I send a task that exceeds time limit
		Then the client should handle the timeout gracefully
		And show appropriate timeout message
		
	Scenario: Client reinitializes without errors
		Given the client has completed several tasks
		When I reinitialize the client
		Then the client should be ready for new tasks
		And previous task results should be cleared