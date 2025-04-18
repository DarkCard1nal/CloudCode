import os
import re
from typing import List, Set, Tuple, Dict, Any
from abc import ABC, abstractmethod


class PythonSecurityChecker(ABC):
	# Dangerous modules to be removed
	DANGEROUS_MODULES: Set[str] = {
	    'eval', 'exec', '__import__', 'importlib', 'imp', 'marshal', 'pickle',
	    'socket', 'ftplib', 'telnetlib', 'paramiko', 'smtplib', 'ssl', 'ctypes',
	    'winreg', 'pycryptodome', 'docker', 'joblib', 'dill', 'shelve', 'yaml',
	    'urllib', 'requests', 'boto3'
	}

	# Safe modules that should not be removed
	SAFE_MODULES: Set[str] = {
	    'math', 'statistics', 'random', 'datetime', 'time', 'collections',
	    'enum', 'dataclasses', 'functools', 'itertools', 'operator', 'string',
	    're', 'json', 'csv', 'sys', 'threading', 'multiprocessing', 'tempfile',
	    'shutil', 'zipfile', 'tarfile', 'uuid', 'hashlib', 'base64', 'secrets',
	    'concurrent', 'http'
	}

	# Dangerous operations and functions
	DANGEROUS_OPERATIONS: Set[str] = {
	    'eval', 'exec', 'compile', 'execfile', 'input', 'system', 'popen',
	    'spawn', 'fork', 'kill', 'terminate', 'check_output', 'call', 'Popen',
	    'run', 'getattr', 'setattr', 'delattr', 'vars', 'dir', 'globals',
	    'locals', '__dict__', 'compile', 'base64.decode', 'bytes.fromhex',
	    'yaml.load', 'yaml.unsafe_load', 'pickle.loads', 'pickle.load',
	    'pickle.dump', 'pickle.dumps', 'joblib.load', 'dill.loads',
	    'marshal.loads'
	}

	# Combined SSRF keywords and patterns
	SSRF_KEYWORDS: Set[str] = {
	    'localhost', '127.0.0.1', '0.0.0.0', '::1', '0x7f000001',
	    '017700000001', '169.254.169.254', 'metadata.google.internal',
	    'file://', 'gopher://', 'dict://'
	}

	# Dangerous URL schemes
	DANGEROUS_URL_SCHEMES: Set[str] = {
	    'file:', 'gopher:', 'dict:', 'ftp:', 'ldap:', 'tftp:', 'smtp:', 'imap:',
	    'pop:', 'news:', 'nntp:', 'telnet:', 'rlogin:', 'rsh:'
	}

	# Dangerous variable names
	DANGEROUS_VARIABLE_NAMES: Set[str] = {
	    'secret', 'password', 'key', 'token', 'credentials', 'private_key',
	    'access_key', 'secret_key', 'AWS_ACCESS_KEY_ID',
	    'AWS_SECRET_ACCESS_KEY', 'api_key', 'admin_password', 'root_password',
	    'publishable_key', 'stripe_api_key'
	}

	# Regex patterns for all types of checks
	REGEX_PATTERNS: List[Tuple[str, str, str]] = [
	    # Network operations
	    (r'socket\.socket\s*\(', 'Socket creation', 'dangerous_operation'),
	    (r'socket\.\w+\s*\(', 'Socket operation', 'dangerous_operation'),
	    (r'urllib\.request\.urlopen\s*\(', 'URL opening',
	     'dangerous_operation'),
	    (r'requests\.(?:get|post|put|delete|head|options|patch)',
	     'HTTP request', 'dangerous_operation'),
	    (r'def\s+(?:download_content|make_request)',
	     'Network access function definition', 'dangerous_operation'),

	    # Pickle operations
	    (r'pickle\.(?:loads|load|dump|dumps)\s*\(',
	     'Pickle serialization/deserialization', 'dangerous_operation'),
	    (r'cPickle\.(?:loads|load|dump|dumps)\s*\(',
	     'Pickle serialization/deserialization', 'dangerous_operation'),

	    # SSRF specific direct checks
	    (r'requests\.(?:get|post|put|delete|head|options|patch)\s*\(\s*[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[?::1\]?|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})',
	     'Direct access to internal network via requests', 'ssrf_attempt'),
	    (r'urllib\.request\.urlopen\s*\(\s*[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[?::1\]?|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|169\.254\.\d{1,3}\.\d{1,3})',
	     'Direct access to internal network via urllib', 'ssrf_attempt'),
	    (r'http\.client\.(?:HTTPConnection|HTTPSConnection)\s*\(\s*[\'"](?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[?::1\]?|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|169\.254\.\d{1,3}\.\d{1,3})',
	     'Direct access to internal network via http.client', 'ssrf_attempt'),

	    # SSRF URL patterns
	    (r'[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)localhost',
	     'URL with localhost', 'ssrf_attempt'),
	    (r'[\'"]https?://127\.0\.0\.1', 'URL with 127.0.0.1', 'ssrf_attempt'),
	    (r'[\'"]https?://0\.0\.0\.0', 'URL with 0.0.0.0', 'ssrf_attempt'),
	    (r'[\'"]https?://\[?::1\]?', 'URL with IPv6 localhost', 'ssrf_attempt'),
	    (r'[\'"]https?://10\.\d{1,3}\.\d{1,3}\.\d{1,3}',
	     'URL with internal 10.x.x.x network', 'ssrf_attempt'),
	    (r'[\'"]https?://172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}',
	     'URL with internal 172.16-31.x.x network', 'ssrf_attempt'),
	    (r'[\'"]https?://192\.168\.\d{1,3}\.\d{1,3}',
	     'URL with internal 192.168.x.x network', 'ssrf_attempt'),
	    (r'[\'"]https?://169\.254\.\d{1,3}\.\d{1,3}',
	     'URL with link-local network', 'ssrf_attempt'),
	    (r'[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)(?:0x7f000001|017700000001)',
	     'URL with obfuscated localhost', 'ssrf_attempt'),
	    (r'[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)169\.254\.169\.254',
	     'URL accessing cloud metadata service', 'ssrf_attempt'),
	    (r'[\'"](https?://|file://|gopher://|dict://|ftp://|ldap://)metadata\.google\.internal',
	     'URL accessing GCP metadata service', 'ssrf_attempt'),

	    # Dangerous URL schemes
	    (r'[\'"]file:///[^\'"]*[\'"]', 'File URL scheme', 'ssrf_attempt'),
	    (r'[\'"]gopher://[^\'"]*[\'"]', 'Gopher URL scheme', 'ssrf_attempt'),
	    (r'[\'"]dict://[^\'"]*[\'"]', 'Dict URL scheme', 'ssrf_attempt'),
	    (r'[\'"]ftp://[^\'"]*[\'"]', 'FTP URL scheme', 'ssrf_attempt'),
	    (r'[\'"]ldap://[^\'"]*[\'"]', 'LDAP URL scheme', 'ssrf_attempt'),
	    (r'[\'"]tftp://[^\'"]*[\'"]', 'TFTP URL scheme', 'ssrf_attempt'),

	    # IP patterns
	    (r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'private IP in 10.x.x.x range',
	     'ssrf_attempt'),
	    (r'172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}',
	     'private IP in 172.16-31.x.x range', 'ssrf_attempt'),
	    (r'192\.168\.\d{1,3}\.\d{1,3}', 'private IP in 192.168.x.x range',
	     'ssrf_attempt'),

	    # Other dangerous operations
	    (r'globals\(\)|locals\(\)', 'Unsafe access to global variables',
	     'dangerous_operation'),
	    (r'lambda\s*:\s*(?:os|sys)', 'Hidden execution of system operations',
	     'dangerous_operation'),

	    # AWS credentials
	    (r'AWS_ACCESS_KEY_ID\s*=', 'AWS Access Key', 'sensitive_data'),
	    (r'AWS_SECRET_ACCESS_KEY\s*=', 'AWS Secret Key', 'sensitive_data'),
	    (r'aws_access_key_id\s*=', 'AWS Access Key', 'sensitive_data'),
	    (r'aws_secret_access_key\s*=', 'AWS Secret Key', 'sensitive_data'),

	    # Stripe API keys
	    (r'stripe\.api_key\s*=', 'Stripe API Key', 'sensitive_data'),
	    (r'publishable_key\s*=', 'Stripe Publishable Key', 'sensitive_data'),
	    (r'[\'"](?:pk|sk)_(?:test|live)_[0-9a-zA-Z]{24,}[\'"]',
	     'Stripe API Key format', 'sensitive_data'),

	    # Cryptography-specific dangers
	    (r'hashlib\.md5\s*\(', 'Insecure hash algorithm MD5', 'insecure_crypto'
	    ),
	    (r'TripleDES', 'Insecure encryption algorithm TripleDES',
	     'insecure_crypto'),
	    (r'cryptography\.hazmat', 'Usage of cryptography hazardous materials',
	     'insecure_crypto'),
	    (r'cryptography\.hazmat\.primitives\.kdf\.pbkdf2\.PBKDF2HMAC\s*\(',
	     'Use of PBKDF2HMAC without proper salt or iterations',
	     'insecure_crypto'),
	    (r'cryptography\.hazmat\.primitives\.ciphers\.Cipher\s*\(',
	     'Use of Cipher without secure key management', 'insecure_crypto'),
	    (r'cryptography\.hazmat\.primitives\.asymmetric\.(?:rsa|ec)\.generate_private_key\s*\(',
	     'Use of key generation without secure parameters', 'insecure_crypto'),
	    (r'cryptography\.hazmat\.primitives\.serialization\.load_(?:pem|der)_private_key\s*\(',
	     'Loading private key without secure password', 'insecure_crypto'),

	    # Multiprocessing-specific dangers
	    (r'multiprocessing\.(?:Process|Pool|Manager|Queue)\s*\(',
	     'Use of multiprocessing without proper resource management',
	     'dangerous_pattern'),

	    # File system operations
	    (r'open\s*\(.*,\s*[\'"](w|a|r\+|w\+|a\+)[\'"]',
	     'File operations without proper validation', 'dangerous_pattern'),

	    # Docker-specific dangers
	    (r'docker\.(?:client|api|from_env|containers|images|networks|volumes)\.|(?:DockerClient|APIClient)\s*\(',
	     'Docker API interaction', 'dangerous_pattern'),

	    # Container escape related checks
	    (r'[\'"]/proc/self/(?:fd|environ|maps|mem|cmdline|status|stat|syscall)',
	     'Access to sensitive /proc files', 'container_escape'),
	    (r'[\'"]/proc/(?:sys|sysrq-trigger|acpi|kcore)',
	     'Access to sensitive /proc paths', 'container_escape'),
	    (r'[\'"](?:/var/run/docker.sock|docker.sock)',
	     'Access to Docker socket', 'container_escape'),
	    (r'[\'"]/dev/(?:mem|kmem|port|tty|pts|console)',
	     'Access to sensitive devices', 'container_escape'),
	    (r'mount -t (?:proc|sysfs|cgroup)', 'Mounting sensitive filesystems',
	     'container_escape'),
	    (r'(?:CVE-\d{4}-\d{4,5}|dirty_(?:cow|pipe)|stack_clash|spectre|meltdown)',
	     'Reference to known vulnerability', 'container_escape'),
	    (r'kernel module|insmod|modprobe', 'Manipulating kernel modules',
	     'container_escape'),
	    (r'dns(?:rebind|exfil|tunnel)', 'DNS-based attack', 'container_escape'),
	    (r'[\'"]/etc/(?:shadow|passwd|ssl|kubernetes)',
	     'Access to critical system files', 'container_escape'),
	    (r'[\'"]/.dockerenv', 'Access to Docker environment file',
	     'container_escape'),

	    # Code obfuscation detection
	    (r'base64\.(?:b64decode|b64encode|b85decode|b32decode)',
	     'Base64 encoding/decoding', 'obfuscation'),
	    (r'bytes\.(?:fromhex|hex)', 'Hex encoding/decoding', 'obfuscation'),
	    (r'(__import__|exec|eval)\s*\(\s*(?:[\'"].*?[\'"]\s*\+|[a-zA-Z_][a-zA-Z0-9_]*\s*\+)',
	     'String concatenation for dynamic execution', 'obfuscation'),
	    (r'(__import__|exec|eval)\s*\(\s*(?:[\'"][^\'\"]+[\'"].encode\([\'"][^\'\"]+[\'"]\))',
	     'Encoded string execution', 'obfuscation'),
	    (r'((?:[\'"][^\'"]*[\'"]\s*\+\s*)+[\'"][^\'"]*[\'"]).decode\([\'"][^\'"]+[\'"]\)',
	     'Concatenated string decoding', 'obfuscation'),
	    (r'(?:join|"".join)\s*\(\s*\[.*?\]\s*\)', 'Array joining',
	     'obfuscation'),
	    (r'(?:chr|ord|unichr)\s*\(\s*\d+\s*\)', 'Character generation',
	     'obfuscation'),
	    (r'(?:\w+)\s*=\s*compile\s*\(\s*.+?\s*,\s*[\'"]<string>[\'"]\s*,',
	     'Dynamic code compilation', 'obfuscation'),

	    # ReDOS vulnerabilities
	    (r're\.compile\s*\(', 'Regular expression compilation', 'redos'),
	    (r're\.compile\s*\(\s*[\'"](?:(?:\([^)]+\)\+)+|\([^)]+\)\*\*|\([^)]+\)\{\d+,\}|\(\.\*\)\+|\.\*\{\d+,\}|(?:\.\*\+)+)[\'"]\s*[,)]',
	     'Regex with nested quantifiers', 'redos'),
	    (r're\.compile\s*\(\s*[\'"](?:\(\.\*\)\.\*|\(\.\*\)\+\.\*|(?:a+)+b|([a-z]+)+|\\1+)[\'"]\s*[,)]',
	     'Regex with catastrophic backtracking', 'redos'),
	    (r'bad_regex', 'Variable name indicates problematic regex', 'redos'),
	    (r're\.compile\s*\(\s*[\'"]\(a\+\)\+b[\'"]\s*[,)]',
	     'Classic ReDOS pattern (a+)+b', 'redos'),

	    # Web framework vulnerabilities
	    (r'(?:flask\.render_template_string|Template|jinja2\.Template|django\.template\.Template|mark_safe|render_template_string)',
	     'Template rendering', 'template_injection'),
	    (r'request\.args', 'Request parameters for template',
	     'template_injection'),
	    (r'(?:flask\.render_template_string|Template|jinja2\.Template|django\.template\.Template|mark_safe|render_template_string)\s*\(\s*(?![\'"]{2})[^)]*?(?:request|input|data|var|param|[\+])',
	     'Template injection from user input', 'template_injection'),
	    (r'render_template_string\s*\(\s*(?:[^\'\"]+[\+]|[\+][^\'\"]+)',
	     'Template injection via string concatenation', 'template_injection'),
	    (r'render_template_string\s*\(\s*template',
	     'Template injection through variable', 'template_injection'),
	    (r'template\s*=\s*[\'"]*<.*>[\'"]*\s*\+\s*.*?request\.',
	     'Template injection via request data concatenation',
	     'template_injection'),
	    (r'template\s*=\s*request\.',
	     'Template injection by direct assignment from request',
	     'template_injection'),
	]

	# Sensitive data pattern detection
	SENSITIVE_DATA_PATTERNS: List[Tuple[str, str]] = [
	    # Credentials and tokens
	    (r'(?i)(?:password|secret\s*key|api_key|github_token|access_token)\s*=',
	     'Potential hardcoded credentials'),
	    (r'(?i)bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*', 'Bearer token exposure'),
	    (r'(?i)(?:key|token|secret|password|credential)\s*=\s*[\'\"][a-zA-Z0-9]{16,}[\'\"]',
	     'Generic credential pattern'),
	    (r'(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
	     'UUID/GUID potential credential'),
	    (r'[\'"]\s*[0-9a-fA-F]{30,}\s*[\'"]',
	     'Hardcoded long hex string (likely API key)'),
	    (r'[\'"][0-9a-zA-Z_\-\.]{30,}[\'"]',
	     'Hardcoded long alphanumeric string (likely credential)'),
	    (r'[\'"]\s*[0-9a-fA-F]{40}\s*[\'"]',
	     'GitHub API key format (40 hex chars)'),
	    (r'[\'"]\s*[0-9a-zA-Z]{20,}\s*[\'"]', 'Generic long credential'),
	]

	def __init__(self, *args, **kwargs):
		"""
		Prevents instantiation of this abstract class.
		"""
		raise TypeError("PythonSecurityChecker is an abstract module and cannot be instantiated")

	@classmethod
	def setup(cls, max_file_size: int = 1024 * 1024, is_docker_environment: bool = False):
		"""
		Configure the security checker parameters.
		
		Args:
			max_file_size (int): Maximum file size in bytes
			is_docker_environment (bool): Flag indicating whether the checker is running in a Docker environment
		
		Returns:
			dict: Configuration details
		"""
		cls.max_file_size = max_file_size
		cls.is_docker_environment = is_docker_environment
		cls.last_unsafe_operations = []

		cls._compiled_regex_patterns = [
		    (re.compile(pattern), description, category)
		    for pattern, description, category in cls.REGEX_PATTERNS
		]
		cls._compiled_sensitive_patterns = [
		    (re.compile(pattern), description)
		    for pattern, description in cls.SENSITIVE_DATA_PATTERNS
		]

		# Dangerous os module functions
		cls.dangerous_os_funcs = set([
		    'system', 'popen', 'execl', 'execle', 'execlp', 'execlpe', 'execv',
		    'execve', 'execvp', 'execvpe', 'spawn', 'spawnl', 'spawnle',
		    'spawnlp', 'spawnlpe', 'spawnv', 'spawnve', 'spawnvp', 'spawnvpe',
		    'fork', 'forkpty', 'kill', 'killpg', 'plock', 'startfile', '_exit'
		])

		# Safe os.path functions
		cls.safe_os_path_funcs = set([
		    'exists', 'isfile', 'isdir', 'islink', 'join', 'abspath', 'dirname',
		    'basename', 'splitext', 'normpath', 'realpath'
		])

		# Dangerous sys module functions
		cls.dangerous_sys_funcs = set([
		    '_getframe', 'setprofile', 'settrace', 'setrecursionlimit', 'exit'
		])

		# Safe sys module functions
		cls.safe_sys_funcs = set(
		    ['argv', 'path', 'platform', 'version', 'version_info', 'modules'])

		# Compile safe subprocess patterns
		cls.safe_subprocess_patterns = [
		    re.compile(r'subprocess\.run\([^)]*shell\s*=\s*False'),
		    re.compile(
		        r'subprocess\.run\([^)]*check\s*=\s*True[^)]*shell\s*=\s*False'
		    ),
		    re.compile(r'subprocess\.check_output\([^)]*shell\s*=\s*False'),
		    re.compile(r'subprocess\.call\([^)]*shell\s*=\s*False'),
		    re.compile(r'subprocess\.run\([^)]*version'),
		    re.compile(r'subprocess\.CompletedProcess'),
		    re.compile(r'subprocess\.PIPE'),
		    re.compile(r'subprocess\.STDOUT')
		]

		# API token prefixes
		cls.api_tokens = {
		    'Slack API': ['xoxb-', 'xoxa-', 'xoxp-', 'xoxs-'],
		    'GitHub API': ['ghp_', 'gho_', 'ghu_', 'github_pat_'],
		    'Stripe API': ['pk_test_', 'sk_test_', 'pk_live_', 'sk_live_']
		}
		
		return {
			"max_file_size": cls.max_file_size,
			"is_docker_environment": cls.is_docker_environment
		}

	@classmethod
	def check_file(cls, file_path: str) -> str:
		"""
		Check a Python file for dangerous code and create a safe version.
		
		Args: 
			file_path (str): Path to the Python file to check
		
		Returns: 
			str: Path to the safe version of the file
		"""
		try:
			cls._validate_file(file_path)

			with open(file_path, 'r', encoding='utf-8') as file:
				content = file.read()

			unsafe_operations, unsafe_lines = cls._detect_unsafe_code(content)
			cls.last_unsafe_operations = unsafe_operations

			safe_content = cls._create_safe_content(content, unsafe_lines)
			safe_file_path = cls._create_safe_file(file_path, safe_content)

			return safe_file_path
		except Exception as e:
			raise ValueError(f"Error checking file: {str(e)}")

	@classmethod
	def get_unsafe_operations(cls) -> List[Dict[str, Any]]:
		""" 
		Returns information about unsafe operations found in the last checked file.
		
		Returns: 
			List[Dict[str, Any]]: List of dictionaries containing information about unsafe operations 
		"""
		return cls.last_unsafe_operations

	@classmethod
	def _validate_file(cls, file_path: str) -> None:
		"""
		Validates the file path and format.
		
		Args:
			file_path (str): Path to the file to check
			
		Raises:
			ValueError: If the file is invalid
		"""
		if not os.path.exists(file_path):
			raise ValueError(f"File not found: {file_path}")

		if not os.path.isfile(file_path):
			raise ValueError(f"Path is not a file: {file_path}")

		if not file_path.endswith('.py'):
			raise ValueError(f"Not a Python file: {file_path}")

		file_size = os.path.getsize(file_path)
		if not hasattr(cls, 'max_file_size'):
			cls.setup()
			
		if file_size > cls.max_file_size:
			raise ValueError(
			    f"File exceeds maximum allowed size ({cls.max_file_size} bytes): {file_size} bytes"
			)

	@classmethod
	def _detect_unsafe_code(
	        cls, content: str) -> Tuple[List[Dict[str, Any]], List[int]]:
		"""
		Optimized method for detecting all types of unsafe code in a single pass.
		
		Args: 
			content (str): File content for analysis
			
		Returns: 
			Tuple[List[Dict[str, Any]], List[int]]: Tuple with a list of unsafe operations and lines
		"""
		if not hasattr(cls, '_compiled_regex_patterns'):
			cls.setup()
			
		lines = content.split('\n')
		unsafe_operations = []
		unsafe_lines = set()

		for i, line in enumerate(lines, 1):
			if i in unsafe_lines:
				continue

			line_lower = line.lower().strip()

			if not line_lower or line_lower.startswith('#'):
				continue

			if 'os.' in line:
				for func in cls.dangerous_os_funcs:
					if f'os.{func}' in line:
						unsafe_lines.add(i)
						unsafe_operations.append({
						    'line':
						        i,
						    'content':
						        line.strip(),
						    'type':
						        'os_dangerous_call',
						    'description':
						        f"Dangerous os module call: os.{func}"
						})
						break

				if i in unsafe_lines:
					continue

			if 'subprocess.' in line and not any(
			    pattern.search(line)
			    for pattern in cls.safe_subprocess_patterns):
				unsafe_lines.add(i)
				unsafe_operations.append({
				    'line': i,
				    'content': line.strip(),
				    'type': 'subprocess_dangerous_call',
				    'description': "Unsafe subprocess call"
				})
				continue

			if any(keyword in line for keyword in cls.SSRF_KEYWORDS):
				keyword = next(k for k in cls.SSRF_KEYWORDS if k in line)
				unsafe_lines.add(i)
				unsafe_operations.append({
				    'line':
				        i,
				    'content':
				        line.strip(),
				    'type':
				        'ssrf_attempt',
				    'description':
				        f"SSRF attempt: Contains potential SSRF keyword '{keyword}'"
				})
				continue

			if 'import ' in line_lower or 'from ' in line_lower:
				for module in cls.DANGEROUS_MODULES:
					if (f'import {module}' in line_lower or
					    f'from {module}' in line_lower or
					    f', {module}' in line_lower or
					    f'{module},' in line_lower):

						unsafe_lines.add(i)
						unsafe_operations.append({
						    'line': i,
						    'content': line.strip(),
						    'type': 'dangerous_import',
						    'description': f"Dangerous module import: {module}"
						})
						break

				if i in unsafe_lines:
					continue

			if any(func in line_lower
			       for func in ['eval(', 'exec(', '__import__(', 'input(']):
				func_name = next(
				    func for func in ['eval', 'exec', '__import__', 'input']
				    if f'{func}(' in line_lower)
				unsafe_lines.add(i)
				unsafe_operations.append({
				    'line': i,
				    'content': line.strip(),
				    'type': 'dangerous_operation',
				    'description': f"Unsafe {func_name} function call"
				})
				continue

			if 'sys.' in line:
				for func in cls.dangerous_sys_funcs:
					if f'sys.{func}' in line:
						unsafe_lines.add(i)
						unsafe_operations.append({
						    'line':
						        i,
						    'content':
						        line.strip(),
						    'type':
						        'sys_dangerous_call',
						    'description':
						        f"Dangerous sys module call: sys.{func}"
						})
						break

				if i in unsafe_lines:
					continue

			for token_type, prefixes in cls.api_tokens.items():
				if any(token in line for token in prefixes):
					unsafe_lines.add(i)
					unsafe_operations.append({
					    'line': i,
					    'content': line.strip(),
					    'type': 'sensitive_data',
					    'description': f"{token_type} token exposure"
					})
					break

			if i in unsafe_lines:
				continue

			for pattern, description, category in cls._compiled_regex_patterns:
				if pattern.search(line):
					unsafe_lines.add(i)
					unsafe_operations.append({
					    'line': i,
					    'content': line.strip(),
					    'type': category,
					    'description': description
					})
					break

			if i in unsafe_lines:
				continue

			for pattern, description in cls._compiled_sensitive_patterns:
				if pattern.search(line):
					unsafe_lines.add(i)
					unsafe_operations.append({
					    'line': i,
					    'content': line.strip(),
					    'type': 'sensitive_data',
					    'description': description
					})
					break

			if 'cryptography.hazmat' in line:
				unsafe_lines.add(i)
				unsafe_operations.append({
				    'line': i,
				    'content': line.strip(),
				    'type': 'insecure_crypto',
				    'description': "Usage of cryptography hazardous materials"
				})

		return unsafe_operations, list(unsafe_lines)

	@classmethod
	def _create_safe_content(cls, content: str,
	                         unsafe_lines: List[int]) -> str:
		"""
		Creates a safe version of the content by filtering out unsafe lines.
		
		Args: 
			content (str): Original content
			unsafe_lines (List[int]): List of line numbers to remove
			
		Returns: 
			str: Safe content
		"""
		lines = content.split('\n')
		safe_lines = []
		unsafe_set = set(unsafe_lines)

		operation_types = {}
		for op in cls.last_unsafe_operations:
			operation_types[op['line']] = op['type']

		for i, line in enumerate(lines, 1):
			if i in unsafe_set:
				if line.strip():
					op_type = operation_types.get(i, 'unknown')
					safe_lines.append(
					    f"# WARNING: Potentially unsafe code removed: {op_type}"
					)
			else:
				safe_lines.append(line)

		return '\n'.join(safe_lines)

	@classmethod
	def _is_safe_import(cls, line: str) -> bool:
		"""
		Determines if an import statement is safe.
		
		Args: 
			line (str): Line to check
			
		Returns: 
			bool: True if the import is safe, False otherwise
		"""
		line_lower = line.lower()

		if not ('import ' in line_lower or 'from ' in line_lower):
			return True

		if ('import os' in line_lower or 'from os' in line_lower or
		    'import subprocess' in line_lower or
		    'from subprocess' in line_lower):
			return True

		for module in cls.SAFE_MODULES:
			if (f'import {module}' in line_lower or
			    f'from {module}' in line_lower or f', {module}' in line_lower or
			    f'{module},' in line_lower):
				return True

		for module in cls.DANGEROUS_MODULES:
			if (f'import {module}' in line_lower or
			    f'from {module}' in line_lower or f', {module}' in line_lower or
			    f'{module},' in line_lower):
				return False

		return cls.is_docker_environment

	@classmethod
	def _create_safe_file(cls, original_path: str, safe_content: str) -> str:
		"""
		Creates a new file with safe content.
		
		Args: 
			original_path (str): Path to the original file
			safe_content (str): Safe content
			
		Returns: 
			str: Path to the new safe file
		"""
		dir_name = os.path.dirname(original_path)
		base_name = os.path.basename(original_path)
		file_name, file_ext = os.path.splitext(base_name)

		safe_file_path = os.path.join(dir_name, f"{file_name}_safe{file_ext}")

		with open(safe_file_path, 'w', encoding='utf-8') as file:
			file.write(safe_content)

		return safe_file_path
