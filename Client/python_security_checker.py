import ast
import os
import re
import tokenize
import io
import keyword
from typing import List, Set, Tuple, Dict, Any, Optional


class PythonSecurityChecker:
	# Dangerous modules that should be removed
	DANGEROUS_MODULES: Set[str] = {
		'os', 'subprocess', 'sys', 'eval', 'exec', 'globals', 'locals',
		'__import__', 'importlib', 'imp', 'marshal', 'pickle', 'socket',
		'ftplib', 'telnetlib', 'urllib', 'http', 'https', 'ssl', 'paramiko', 
		'requests', 'cryptography', 'smtplib', 'zipfile', 'tarfile', 
		'shutil', 'tempfile', 'multiprocessing', 'ctypes', 'mmap', 
		'signal', 'threading', 'concurrent', 'winreg', 'secrets',
		'base64', 'uuid', 'hashlib', 'cryptography', 'pycryptodome', 
		'jwt', 'nacl', 'werkzeug', 'aiohttp'
	}
	
	# Safe modules that should not be removed
	SAFE_MODULES: Set[str] = {
		'math', 'statistics', 'random', 'datetime', 'time',
		'collections', 'enum', 'dataclasses', 'functools', 'itertools',
		'operator', 'string', 're', 'json', 'csv'
	}
	
	# Dangerous operations and functions
	DANGEROUS_OPERATIONS: Set[str] = {
		'eval', 'exec', 'compile', 'execfile', 'input', 'raw_input',
		'system', 'popen', 'spawn', 'fork', 'kill', 'terminate',
		'check_output', 'call', 'Popen', 'run', 'send', 'sendall', 
		'sendto', 'recv', 'connect', 'bind', 'listen', 'accept',
		'open', 'read', 'write', 'remove', 'rmdir', 'chmod', 
		'chown', 'mkdir', 'makedirs', 'symlink', 'link',
		'getattr', 'setattr', 'delattr', 'vars', 'dir', 
		'globals', 'locals', '__dict__', 'compile'
	}

	# Regular expressions for finding dangerous patterns
	DANGEROUS_REGEX_PATTERNS: List[Tuple[str, str]] = [
		# System operations
		(r'os\.system\s*\(', 'Execution of system commands'),
		(r'subprocess\..*\(', 'Subprocess call'),
		(r'\bsystem\s*\(', 'Execution of system commands'),
		(r'exec\s*\(', 'Execution of dynamic code'),
		(r'eval\s*\(', 'Unsafe expression evaluation'),
		(r'__import__\s*\(', 'Dynamic importing'),
		(r'input\s*\(', 'Unsafe input reception'),
		(r'\braw_input\s*\(', 'Deprecated and unsafe input method'),
		
		# Network operations
		(r'socket\.socket\s*\(', 'Socket creation'),
		(r'socket\.\w+\s*\(', 'Socket operation'),
		(r'\.connect\s*\(', 'Network connection'),
		(r'\.bind\s*\(', 'Socket binding'),
		(r'\.listen\s*\(', 'Socket listening'),
		(r'\.accept\s*\(', 'Socket accepting connections'),
		(r'(?:urllib\.request\.urlopen|requests\.get)', 'External HTTP requests'),
		
		# File operations
		(r'open\s*\(\s*[\'"].*?[\'"].*?mode\s*=\s*[\'"]w[\'"]', 'File write operation'),
		(r'open\s*\(\s*[\'"].*?[\'"].*?[\'"]w[\'"]', 'File write operation'),
		(r'open\s*\(\s*[\'"](.*?)[\'"]\s*,\s*[\'"](w|a|x)', 'File write operation'),
		(r'(?:chmod|chown)\s*\(', 'Changing file access permissions'),
		
		# Serialization
		(r'pickle\.loads\s*\(', 'Pickle deserialization'),
		(r'pickle\.load\s*\(', 'Pickle deserialization'),
		(r'cPickle\.loads\s*\(', 'Pickle deserialization'),
		(r'cPickle\.load\s*\(', 'Pickle deserialization'),
		
		# Other dangerous operations
		(r'globals\(\)|locals\(\)', 'Unsafe access to global variables'),
		(r'lambda\s*:\s*(?:os|sys)', 'Hidden execution of system operations'),
		(r'\.\./', 'Possible directory traversal')
	]
	
	# Regular expressions for finding sensitive data
	SENSITIVE_DATA_PATTERNS: List[Tuple[str, str]] = [
		# Passwords and keys
		(r'(?i)password\s*=', 'Potential hardcoded passwords'),
		(r'(?i)secret\s*key', 'Possible disclosure of secret keys'),
		(r'(?i)api_key\s*=', 'API key exposure'),
		(r'(?i)github_token\s*=', 'GitHub token exposure'),
		(r'(?i)access_token\s*=', 'Access token exposure'),
		(r'(?i)bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*', 'Bearer token exposure'),
		(r'(?i)(?:key|token|secret|password|credential)\s*=\s*[\'\"][a-zA-Z0-9]{16,}[\'\"]', 'Generic credential pattern'),
		
		# API keys for specific services
		(r'GITHUB_API_KEY\s*=', 'GitHub API key exposure'),
		(r'(?i)github_api_key\s*=\s*[\'\"][0-9a-zA-Z]{35,40}[\'\"]', 'GitHub API key exposure'),
		(r'(?i)(gh[opsu]_[0-9a-zA-Z]{36,255})', 'GitHub Personal Access Token exposure'),
		(r'(?i)(github_pat_[0-9a-zA-Z]{22,255})', 'GitHub Fine-grained Access Token exposure'),
		(r'(?i)(xox[pboa]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})', 'Slack API Token'),
		(r'(?i)(sk_live_[0-9a-z]{24})', 'Stripe Secret Key'),
		(r'(?i)(pk_live_[0-9a-z]{24})', 'Stripe Publishable Key'),
		(r'(?i)([a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+@github\.com)', 'GitHub credentials in URL'),
		
		# General patterns
		(r'(?i)([a-zA-Z0-9]{40})', 'Potential API key or token (40 chars)'),
		(r'(?i)(api[-_]?key|auth[-_]?token|access[-_]?token|secret[-_]?key|app[-_]?key)[\s]*[=:][\s]*[\'\"][0-9a-zA-Z]{16,}[\'\"]', 'Generic API key or token'),
		(r'(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', 'UUID/GUID potential credential'),
		(r'[\'"]\s*[0-9a-fA-F]{30,}\s*[\'"]', 'Hardcoded long hex string (likely API key)'),
		(r'[\'"][0-9a-zA-Z_\-\.]{30,}[\'"]', 'Hardcoded long alphanumeric string (likely credential)'),
		(r'[\'"]\s*[0-9a-fA-F]{40}\s*[\'"]', 'GitHub API key format (40 hex chars)'),
		(r'[\'"]\s*[0-9a-zA-Z]{20,}\s*[\'"]', 'Generic long credential'),
		(r'[\'"][a-zA-Z0-9+/]{60,}={0,2}[\'"]', 'Base64 encoded data (potentially sensitive)'),
		
		# Specific keywords
		(r'(?i)AWS_(?:SECRET_)?ACCESS_KEY', 'AWS credential reference'),
		(r'(?i)account_?key', 'Account key reference'),
		(r'(?i)(?:client|api|auth|webhook)_?secret', 'Secret key reference'),
		(r'(?i)passwd', 'Password alias'),
		(r'(?i)private key', 'Private key reference'),
		(r'(?i)BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY', 'Private key header')
	]

	# Forbidden variable names
	DANGEROUS_VARIABLE_NAMES: Set[str] = {
		'secret', 'password', 'key', 'token', 'credentials', 
		'private_key', 'access_key', 'secret_key', 
		'api_key', 'admin_password', 'root_password'
	}

	def __init__(self, max_file_size: int = 1024 * 1024):  # 1 MB by default
		self.max_file_size = max_file_size
		self.last_unsafe_operations = []
		
	def check_file(self, file_path: str) -> str:
		""" Checks a Python file for dangerous code and creates a safe version.
		Args: file_path (str): Path to the file to check  
		Returns: str: Path to the newly created safe file
		Raises: ValueError: If the file is not found, is not a Python file, or exceeds the maximum size
		"""
		try:
			self._validate_file(file_path)
		except ValueError as e:
			error_msg = str(e)
			if "File not found" in error_msg:
				raise ValueError(f"File not found: {file_path}")
			elif "Not a Python file" in error_msg:
				raise ValueError(f"Not a Python file: {file_path}")
			else:
				raise e

		with open(file_path, 'r', encoding='utf-8') as file:
			content = file.read()

		unsafe_operations, unsafe_lines = self._detect_unsafe_code(content)
		
		self.last_unsafe_operations = unsafe_operations
		
		safe_content = self._create_safe_content(content, unsafe_lines)
		
		safe_file_path = self._create_safe_file(file_path, safe_content)

		return safe_file_path
	
	def get_unsafe_operations(self) -> List[Dict[str, Any]]:
		""" Returns information about unsafe operations found in the last checked file.
		Returns: List[Dict[str, Any]]: List of dictionaries containing information about unsafe operations """
		return self.last_unsafe_operations
	
	def _validate_file(self, file_path: str) -> None:
		"""Validates the file path and format."""
		if not os.path.exists(file_path):
			raise ValueError(f"File not found: {file_path}")
		
		if not os.path.isfile(file_path):
			raise ValueError(f"Path is not a file: {file_path}")

		if not file_path.endswith('.py'):
			raise ValueError(f"Not a Python file: {file_path}")

		file_size = os.path.getsize(file_path)
		if file_size > self.max_file_size:
			raise ValueError(f"File exceeds maximum allowed size ({self.max_file_size} bytes): {file_size} bytes")
	
	def _detect_unsafe_code(self, content: str) -> Tuple[List[Dict[str, Any]], List[int]]:
		"""
		Comprehensive method for detecting all types of unsafe code.
		Args: content (str): File content for analysis
		Returns: Tuple[List[Dict[str, Any]], List[int]]: Tuple with a list of unsafe operations and lines
		"""
		lines = content.split('\n')
		unsafe_operations = []
		unsafe_lines = set()
		
		for i, line in enumerate(lines, 1):
			line_lower = line.lower().strip()
			is_unsafe = False
			
			if 'import ' in line_lower or 'from ' in line_lower:
				for module in self.DANGEROUS_MODULES:
					if (f'import {module}' in line_lower or 
						f'from {module}' in line_lower or 
						f', {module}' in line_lower or 
						f'{module},' in line_lower):
						
						is_unsafe = True
						unsafe_lines.add(i)
						unsafe_operations.append({
							'line': i,
							'content': line.strip(),
							'type': 'dangerous_import',
							'description': f"Dangerous module import: {module}"
						})
						break
			
			if is_unsafe:
				continue
			
			if 'xoxb-' in line or 'xoxa-' in line or 'xoxp-' in line or 'xoxs-' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
					'line': i,
					'content': line.strip(),
					'type': 'sensitive_data',
					'description': "Slack API token exposure"
				})
				continue
				
			if 'ghp_' in line or 'gho_' in line or 'ghu_' in line or 'github_pat_' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
					'line': i,
					'content': line.strip(),
					'type': 'sensitive_data',
					'description': "GitHub API token exposure"
				})
				continue
			
			if 'input(' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
					'line': i,
					'content': line.strip(),
					'type': 'dangerous_operation',
					'description': "Unsafe input() function call"
				})
				continue
			
			if '__import__(' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
					'line': i,
					'content': line.strip(),
					'type': 'hidden_import',
					'description': "Hidden import via __import__"
				})
				continue
			
			if 'eval(' in line or 'exec(' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
					'line': i,
					'content': line.strip(),
					'type': 'dangerous_execution',
					'description': "Dangerous code execution via eval/exec"
				})
				continue
				
			if 'open(' in line and ('w' in line or 'a' in line or 'x' in line):
				if re.search(r'open\s*\(\s*[\'"](.*?)[\'"]\s*,\s*[\'"](w|a|x)', line):
					unsafe_lines.add(i)
					unsafe_operations.append({
						'line': i,
						'content': line.strip(),
						'type': 'file_operation',
						'description': "File write operation"
					})
					continue
		
		for i, line in enumerate(lines, 1):
			if i in unsafe_lines:
				continue
				
			for pattern, description in self.DANGEROUS_REGEX_PATTERNS:
				if re.search(pattern, line):
					unsafe_lines.add(i)
					unsafe_operations.append({
						'line': i,
						'content': line.strip(),
						'type': 'dangerous_pattern',
						'description': description
					})
					break
		
		for i, line in enumerate(lines, 1):
			if i in unsafe_lines:
				continue
				
			for pattern, description in self.SENSITIVE_DATA_PATTERNS:
				if re.search(pattern, line):
					unsafe_lines.add(i)
					unsafe_operations.append({
						'line': i,
						'content': line.strip(),
						'type': 'sensitive_data',
						'description': description
					})
					break
			
			if '=' in line:
				var_name = line.split('=')[0].strip()
				if var_name.lower() in self.DANGEROUS_VARIABLE_NAMES:
					unsafe_lines.add(i)
					unsafe_operations.append({
						'line': i,
						'content': line.strip(),
						'type': 'sensitive_variable',
						'description': f"Sensitive variable: {var_name}"
					})
		
		return unsafe_operations, list(unsafe_lines)
	
	def _create_safe_content(self, content: str, unsafe_lines: List[int]) -> str:
		""" Removes unsafe lines from the file content.
		Args: 
			content (str): Original file content
			unsafe_lines (List[int]): List of unsafe line numbers
		Returns: str: Safe file content """
		if not unsafe_lines:
			return content

		lines = content.split('\n')
		safe_lines = []
		
		unsafe_lines_set = set(unsafe_lines)
		
		for i, line in enumerate(lines, 1):
			if i in unsafe_lines_set:
				continue
			
			if self._is_safe_import(line):
				safe_lines.append(line)
				continue
				
			if self._is_line_unsafe(line):
				continue
				
			safe_lines.append(line)
				
		if not safe_lines:
			return "# All code was removed due to security concerns\n# This is a safe empty file."
			
		return '\n'.join(safe_lines)
	
	def _is_safe_import(self, line: str) -> bool:
		""" Checks if an import is safe (e.g., math).
		Args: line (str): Line to check
		Returns: bool: True if it's a safe import that should be kept
		"""
		line_lower = line.lower().strip()
		
		if 'import ' in line_lower or 'from ' in line_lower:
			for module in self.SAFE_MODULES:
				if (f'import {module}' in line_lower or 
					f'from {module}' in line_lower or 
					f', {module}' in line_lower or 
					f'{module},' in line_lower):
					return True
		return False
	
	def _is_line_unsafe(self, line: str) -> bool:
		""" Checks a line for dangerous code.
		Args: line (str): Line to check
		Returns: bool: True if the line contains dangerous code, otherwise False
		"""
		line_lower = line.lower()
		
		if 'import ' in line_lower or 'from ' in line_lower:
			for module in self.DANGEROUS_MODULES:
				if (f'import {module}' in line_lower or 
					f'from {module}' in line_lower or 
					f', {module}' in line_lower or 
					f'{module},' in line_lower):
					return True
		
		if any(op in line for op in ['eval(', 'exec(', 'system(', '__import__(', 'input(']):
			return True
		
		if any(op in line for op in ['os.system', 'os.listdir', 'subprocess.', 'socket.', '.socket(']):
			return True
		
		if 'open(' in line and ('w' in line or 'a' in line or 'x' in line):
			if re.search(r'open\s*\(\s*[\'"](.*?)[\'"]\s*,\s*[\'"](w|a|x)', line):
				return True
		
		if any(op in line_lower for op in ['urllib', 'requests.', '.connect(', '.bind(', '.listen(', '.socket(']):
			return True
		
		if 'pickle.' in line_lower:
			return True
		
		if 'github_api_key' in line_lower or 'GITHUB_API_KEY' in line:
			return True
		
		if 'stripe_secret_key' in line_lower or 'STRIPE_SECRET_KEY' in line:
			return True
			
		if any(token in line for token in ['ghp_', 'gho_', 'ghu_', 'github_pat_', 
										 'sk_test_', 'sk_live_', 'pk_test_', 'pk_live_',
										 'xoxb-', 'xoxa-', 'xoxp-', 'xoxs-']):
			return True
			
		for pattern, _ in self.SENSITIVE_DATA_PATTERNS:
			if re.search(pattern, line):
				return True
			
		for pattern, _ in self.DANGEROUS_REGEX_PATTERNS:
			if re.search(pattern, line):
				return True
		
		return False
	
	def _create_safe_file(self, original_path: str, safe_content: str) -> str:
		""" Creates a file with safe content.
		Args: 
			original_path (str): Path to the original file
			safe_content (str): Safe content
		Returns: str: Path to the created safe file
		"""
		directory = os.path.dirname(original_path)
		filename = os.path.basename(original_path)
		
		base, ext = os.path.splitext(filename)
		safe_filename = f"{base}_safe{ext}"
		safe_path = os.path.join(directory, safe_filename)
		
		counter = 1
		while os.path.exists(safe_path):
			safe_filename = f"{base}_safe_{counter}{ext}"
			safe_path = os.path.join(directory, safe_filename)
			counter += 1
		
		with open(safe_path, 'w', encoding='utf-8') as file:
			file.write(safe_content)

		return safe_path