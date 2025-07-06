#!/usr/bin/env python3
"""
CORS and Error Handling Tests
Tests for Cross-Origin Resource Sharing and comprehensive error handling
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import aiohttp
import random
import string

from test_base import TestSuite as BaseTestSuite, TestResult

class TestSuite:
    """CORS and Error Handling Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("CORS & Error Handling", "Tests for CORS compliance and comprehensive error handling")
        
    async def run(self):
        """Run all CORS and error handling tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # CORS tests
        await self.test_cors_preflight_all_endpoints()
        await self.test_cors_simple_requests()
        await self.test_cors_with_credentials()
        await self.test_cors_origin_validation()
        await self.test_cors_method_validation()
        await self.test_cors_header_validation()
        await self.test_cors_max_age()
        
        # Error handling tests
        await self.test_404_not_found()
        await self.test_405_method_not_allowed()
        await self.test_400_bad_request()
        await self.test_500_internal_server_error()
        await self.test_413_payload_too_large()
        await self.test_415_unsupported_media_type()
        await self.test_429_rate_limiting()
        
        # Error response structure tests
        await self.test_error_response_structure()
        await self.test_error_message_consistency()
        await self.test_error_codes_mapping()
        
        # Edge cases and malformed requests
        await self.test_malformed_json()
        await self.test_invalid_content_type()
        await self.test_missing_required_headers()
        await self.test_extremely_long_urls()
        await self.test_invalid_http_methods()
        
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
                           expect_cors: bool = False, raw_body: str = None) -> tuple:
        """Make HTTP request and return (status, response, duration, response_headers)"""
        url = f"{self.api_base_url}{endpoint}"
        request_headers = headers or {}
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Prepare request data
                if raw_body is not None:
                    request_data = raw_body
                elif data is not None:
                    request_data = json.dumps(data)
                else:
                    request_data = None
                
                async with session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    data=request_data,
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

    def _get_test_origins(self) -> List[str]:
        """Get list of origins to test CORS with"""
        return [
            'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
            'https://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
            'http://localhost:3000',
            'http://localhost:8080',
            'https://localhost:3000',
            'https://example.com',
            'http://malicious-site.com',
            'null',  # File protocol
            ''  # Empty origin
        ]

    def _get_test_endpoints(self) -> List[str]:
        """Get list of endpoints to test"""
        return [
            '/configurations',
            '/rounds',
            '/scores',
            '/user/profile',
            '/rounds/solved',
            '/rounds/baseline',
            '/rounds/user-submitted'
        ]

    async def test_cors_preflight_all_endpoints(self):
        """Test CORS preflight requests for all endpoints"""
        start_time = time.time()
        
        try:
            endpoints = self._get_test_endpoints()
            valid_origins = [
                'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
                'https://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            ]
            
            successful_preflights = 0
            total_tests = len(endpoints) * len(valid_origins)
            
            for endpoint in endpoints:
                for origin in valid_origins:
                    headers = {
                        'Origin': origin,
                        'Access-Control-Request-Method': 'GET',
                        'Access-Control-Request-Headers': 'authorization,content-type'
                    }
                    
                    status, response, req_duration, resp_headers = await self._make_request('OPTIONS', endpoint, headers)
                    
                    if status == 200:
                        # Check for required CORS headers
                        cors_headers = [
                            'access-control-allow-origin',
                            'access-control-allow-methods',
                            'access-control-allow-headers'
                        ]
                        
                        has_cors_headers = all(
                            header in [h.lower() for h in resp_headers.keys()] 
                            for header in cors_headers
                        )
                        
                        if has_cors_headers:
                            successful_preflights += 1
            
            duration = time.time() - start_time
            success_rate = (successful_preflights / total_tests) * 100 if total_tests > 0 else 0
            
            if success_rate >= 70:  # At least 70% should work
                result = TestResult("test_cors_preflight_all_endpoints", "PASS", duration, 
                                  f"CORS preflight working: {successful_preflights}/{total_tests} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_cors_preflight_all_endpoints", "FAIL", duration, 
                                  f"CORS preflight poor coverage: {successful_preflights}/{total_tests} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_preflight_all_endpoints", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_simple_requests(self):
        """Test CORS simple requests (GET with simple headers)"""
        start_time = time.time()
        
        try:
            valid_origin = 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            
            headers = {
                'Origin': valid_origin,
                'Accept': 'application/json'
            }
            
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
            
            # Check if Access-Control-Allow-Origin is present in response
            cors_origin = resp_headers.get('access-control-allow-origin') or resp_headers.get('Access-Control-Allow-Origin')
            
            duration = time.time() - start_time
            if cors_origin:
                result = TestResult("test_cors_simple_requests", "PASS", duration, 
                                  f"CORS simple request working, origin: {cors_origin}")
            else:
                result = TestResult("test_cors_simple_requests", "FAIL", duration, 
                                  "CORS simple request missing Access-Control-Allow-Origin header")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_simple_requests", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_with_credentials(self):
        """Test CORS requests with credentials"""
        start_time = time.time()
        
        try:
            valid_origin = 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            
            headers = {
                'Origin': valid_origin,
                'Authorization': 'Bearer test-token'
            }
            
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
            
            # Check CORS headers related to credentials
            allow_credentials = resp_headers.get('access-control-allow-credentials') or resp_headers.get('Access-Control-Allow-Credentials')
            allow_origin = resp_headers.get('access-control-allow-origin') or resp_headers.get('Access-Control-Allow-Origin')
            
            duration = time.time() - start_time
            if allow_origin and (allow_credentials == 'true' or allow_origin != '*'):
                result = TestResult("test_cors_with_credentials", "PASS", duration, 
                                  f"CORS credentials handling appropriate: credentials={allow_credentials}, origin={allow_origin}")
            else:
                result = TestResult("test_cors_with_credentials", "FAIL", duration, 
                                  f"CORS credentials handling issue: credentials={allow_credentials}, origin={allow_origin}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_with_credentials", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_origin_validation(self):
        """Test CORS origin validation"""
        start_time = time.time()
        
        try:
            test_origins = self._get_test_origins()
            results = {}
            
            for origin in test_origins:
                headers = {'Origin': origin}
                status, response, req_duration, resp_headers = await self._make_request('OPTIONS', '/configurations', headers)
                
                allow_origin = resp_headers.get('access-control-allow-origin') or resp_headers.get('Access-Control-Allow-Origin')
                results[origin] = {
                    'status': status,
                    'allowed_origin': allow_origin
                }
            
            # Analyze results
            valid_origins = [
                'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
                'https://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            ]
            
            correctly_allowed = 0
            correctly_rejected = 0
            
            for origin, result in results.items():
                if origin in valid_origins and result['allowed_origin']:
                    correctly_allowed += 1
                elif origin not in valid_origins and not result['allowed_origin']:
                    correctly_rejected += 1
            
            duration = time.time() - start_time
            total_correct = correctly_allowed + correctly_rejected
            
            if total_correct >= len(test_origins) * 0.7:  # 70% correct handling
                result = TestResult("test_cors_origin_validation", "PASS", duration, 
                                  f"Origin validation working: {total_correct}/{len(test_origins)} correct")
            else:
                result = TestResult("test_cors_origin_validation", "FAIL", duration, 
                                  f"Origin validation issues: only {total_correct}/{len(test_origins)} correct")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_origin_validation", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_method_validation(self):
        """Test CORS method validation"""
        start_time = time.time()
        
        try:
            valid_origin = 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            test_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'CONNECT', 'TRACE']
            
            allowed_methods = []
            
            for method in test_methods:
                headers = {
                    'Origin': valid_origin,
                    'Access-Control-Request-Method': method,
                    'Access-Control-Request-Headers': 'content-type'
                }
                
                status, response, req_duration, resp_headers = await self._make_request('OPTIONS', '/configurations', headers)
                
                if status == 200:
                    allow_methods = resp_headers.get('access-control-allow-methods') or resp_headers.get('Access-Control-Allow-Methods')
                    if allow_methods and method.upper() in allow_methods.upper():
                        allowed_methods.append(method)
            
            duration = time.time() - start_time
            
            # Should at least allow GET and POST
            required_methods = ['GET', 'POST']
            has_required = all(method in allowed_methods for method in required_methods)
            
            if has_required:
                result = TestResult("test_cors_method_validation", "PASS", duration, 
                                  f"CORS method validation working: {len(allowed_methods)} methods allowed")
            else:
                result = TestResult("test_cors_method_validation", "FAIL", duration, 
                                  f"CORS method validation issues: only {allowed_methods} allowed")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_method_validation", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_header_validation(self):
        """Test CORS header validation"""
        start_time = time.time()
        
        try:
            valid_origin = 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            test_headers = [
                'authorization',
                'content-type',
                'accept',
                'x-requested-with',
                'x-custom-header',
                'x-dangerous-header'
            ]
            
            allowed_headers = []
            
            for header in test_headers:
                headers = {
                    'Origin': valid_origin,
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': header
                }
                
                status, response, req_duration, resp_headers = await self._make_request('OPTIONS', '/configurations', headers)
                
                if status == 200:
                    allow_headers = resp_headers.get('access-control-allow-headers') or resp_headers.get('Access-Control-Allow-Headers')
                    if allow_headers and header.lower() in allow_headers.lower():
                        allowed_headers.append(header)
            
            duration = time.time() - start_time
            
            # Should at least allow authorization and content-type
            required_headers = ['authorization', 'content-type']
            has_required = all(header in allowed_headers for header in required_headers)
            
            if has_required:
                result = TestResult("test_cors_header_validation", "PASS", duration, 
                                  f"CORS header validation working: {len(allowed_headers)} headers allowed")
            else:
                result = TestResult("test_cors_header_validation", "FAIL", duration, 
                                  f"CORS header validation issues: only {allowed_headers} allowed")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_header_validation", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_max_age(self):
        """Test CORS max-age header"""
        start_time = time.time()
        
        try:
            valid_origin = 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com'
            
            headers = {
                'Origin': valid_origin,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'authorization,content-type'
            }
            
            status, response, req_duration, resp_headers = await self._make_request('OPTIONS', '/configurations', headers)
            
            max_age = resp_headers.get('access-control-max-age') or resp_headers.get('Access-Control-Max-Age')
            
            duration = time.time() - start_time
            if max_age:
                try:
                    max_age_value = int(max_age)
                    if 0 <= max_age_value <= 86400:  # Reasonable range (0 to 24 hours)
                        result = TestResult("test_cors_max_age", "PASS", duration, 
                                          f"CORS max-age header present: {max_age} seconds")
                    else:
                        result = TestResult("test_cors_max_age", "FAIL", duration, 
                                          f"CORS max-age value unreasonable: {max_age}")
                except ValueError:
                    result = TestResult("test_cors_max_age", "FAIL", duration, 
                                      f"CORS max-age not a valid number: {max_age}")
            else:
                result = TestResult("test_cors_max_age", "PASS", duration, 
                                  "CORS max-age header not set (browsers will use default)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_max_age", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_404_not_found(self):
        """Test 404 Not Found responses"""
        start_time = time.time()
        
        try:
            not_found_urls = [
                '/nonexistent',
                '/configurations/does-not-exist',
                '/rounds/invalid-round-id',
                '/scores/nonexistent-round',
                '/user/nonexistent',
                '/api/v2/configurations',  # Wrong API version
                '/configurations/../../etc/passwd'  # Path traversal attempt
            ]
            
            proper_404s = 0
            
            for url in not_found_urls:
                status, response, req_duration, resp_headers = await self._make_request('GET', url)
                
                if status == 404:
                    proper_404s += 1
                elif status in [401, 403]:  # Also acceptable (auth required first)
                    proper_404s += 0.5  # Partial credit
            
            duration = time.time() - start_time
            success_rate = (proper_404s / len(not_found_urls)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_404_not_found", "PASS", duration, 
                                  f"404 handling working: {proper_404s}/{len(not_found_urls)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_404_not_found", "FAIL", duration, 
                                  f"404 handling issues: only {proper_404s}/{len(not_found_urls)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_404_not_found", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_405_method_not_allowed(self):
        """Test 405 Method Not Allowed responses"""
        start_time = time.time()
        
        try:
            # Test unsupported methods on known endpoints
            method_tests = [
                ('PATCH', '/configurations'),
                ('DELETE', '/scores'),
                ('HEAD', '/user/profile'),
                ('TRACE', '/rounds'),
                ('CONNECT', '/configurations')
            ]
            
            proper_405s = 0
            
            for method, endpoint in method_tests:
                status, response, req_duration, resp_headers = await self._make_request(method, endpoint)
                
                if status == 405:
                    proper_405s += 1
                elif status in [401, 403, 404]:  # Also acceptable
                    proper_405s += 0.5  # Partial credit
            
            duration = time.time() - start_time
            success_rate = (proper_405s / len(method_tests)) * 100
            
            if success_rate >= 50:  # Lower threshold as some methods might be supported
                result = TestResult("test_405_method_not_allowed", "PASS", duration, 
                                  f"405 handling working: {proper_405s}/{len(method_tests)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_405_method_not_allowed", "FAIL", duration, 
                                  f"405 handling issues: only {proper_405s}/{len(method_tests)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_405_method_not_allowed", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_400_bad_request(self):
        """Test 400 Bad Request responses"""
        start_time = time.time()
        
        try:
            # Test various bad requests
            bad_requests = [
                ('POST', '/configurations', {'Content-Type': 'application/json'}, '{"invalid": json}'),  # Invalid JSON
                ('POST', '/rounds', {'Content-Type': 'application/json'}, '{}'),  # Empty object
                ('PUT', '/user/profile', {'Content-Type': 'application/json'}, '{"username": 123}'),  # Wrong type
                ('POST', '/scores', {'Content-Type': 'application/json'}, '{"moves": -1}'),  # Invalid value
            ]
            
            proper_400s = 0
            
            for method, endpoint, headers, body in bad_requests:
                status, response, req_duration, resp_headers = await self._make_request(method, endpoint, headers, raw_body=body)
                
                if status == 400:
                    proper_400s += 1
                elif status in [401, 403]:  # Auth might be checked first
                    proper_400s += 0.5  # Partial credit
            
            duration = time.time() - start_time
            success_rate = (proper_400s / len(bad_requests)) * 100
            
            if success_rate >= 50:
                result = TestResult("test_400_bad_request", "PASS", duration, 
                                  f"400 handling working: {proper_400s}/{len(bad_requests)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_400_bad_request", "FAIL", duration, 
                                  f"400 handling issues: only {proper_400s}/{len(bad_requests)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_400_bad_request", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_500_internal_server_error(self):
        """Test handling of potential server errors"""
        start_time = time.time()
        
        try:
            # Test requests that might trigger server errors
            potential_500s = [
                ('POST', '/configurations', {'Content-Type': 'application/json'}, '{"name": "' + 'x' * 100000 + '"}'),  # Very large data
                ('GET', '/rounds/' + 'x' * 1000),  # Very long ID
                ('POST', '/scores', {'Content-Type': 'application/json'}, '{"roundId": null, "moves": null}'),  # Null values
            ]
            
            no_500_errors = 0
            
            for method, endpoint, headers, body in potential_500s:
                status, response, req_duration, resp_headers = await self._make_request(method, endpoint, headers, raw_body=body)
                
                # Should not return 500 (should handle gracefully with 400, 401, etc.)
                if status != 500:
                    no_500_errors += 1
            
            duration = time.time() - start_time
            success_rate = (no_500_errors / len(potential_500s)) * 100
            
            if success_rate >= 80:
                result = TestResult("test_500_internal_server_error", "PASS", duration, 
                                  f"Server error handling good: {no_500_errors}/{len(potential_500s)} handled gracefully ({success_rate:.1f}%)")
            else:
                result = TestResult("test_500_internal_server_error", "FAIL", duration, 
                                  f"Server error handling issues: only {no_500_errors}/{len(potential_500s)} handled gracefully ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_500_internal_server_error", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_413_payload_too_large(self):
        """Test 413 Payload Too Large responses"""
        start_time = time.time()
        
        try:
            # Create very large payloads
            large_string = 'x' * (10 * 1024 * 1024)  # 10MB string
            large_payload = {
                'name': 'Large Configuration',
                'data': large_string,
                'walls': ['1,1,top'] * 100000,  # Many walls
                'metadata': {f'field_{i}': large_string[:1000] for i in range(1000)}  # Many fields
            }
            
            headers = {'Content-Type': 'application/json'}
            status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, large_payload)
            
            duration = time.time() - start_time
            
            # Should either reject with 413 or handle gracefully with other error codes
            if status in [413, 400, 401, 403]:
                result = TestResult("test_413_payload_too_large", "PASS", duration, 
                                  f"Large payload handled appropriately (status: {status})")
            elif status is None:
                result = TestResult("test_413_payload_too_large", "PASS", duration, 
                                  "Large payload rejected at network level (timeout/connection error)")
            else:
                result = TestResult("test_413_payload_too_large", "FAIL", duration, 
                                  f"Large payload unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_413_payload_too_large", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_415_unsupported_media_type(self):
        """Test 415 Unsupported Media Type responses"""
        start_time = time.time()
        
        try:
            # Test various unsupported content types
            unsupported_types = [
                'text/plain',
                'application/xml',
                'multipart/form-data',
                'application/x-www-form-urlencoded',
                'image/jpeg',
                'text/html',
                'application/octet-stream'
            ]
            
            proper_rejections = 0
            
            for content_type in unsupported_types:
                headers = {'Content-Type': content_type}
                data_body = 'test data'
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, raw_body=data_body)
                
                if status in [415, 400, 401, 403]:  # Any appropriate rejection
                    proper_rejections += 1
            
            duration = time.time() - start_time
            success_rate = (proper_rejections / len(unsupported_types)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_415_unsupported_media_type", "PASS", duration, 
                                  f"Media type validation working: {proper_rejections}/{len(unsupported_types)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_415_unsupported_media_type", "FAIL", duration, 
                                  f"Media type validation issues: only {proper_rejections}/{len(unsupported_types)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_415_unsupported_media_type", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_429_rate_limiting(self):
        """Test 429 Too Many Requests (rate limiting)"""
        start_time = time.time()
        
        try:
            # Send many requests quickly
            responses = []
            
            for i in range(20):
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations')
                responses.append(status)
                
                # Very small delay
                await asyncio.sleep(0.05)
            
            # Check if any rate limiting occurred
            rate_limited = any(status == 429 for status in responses if status is not None)
            
            duration = time.time() - start_time
            
            if rate_limited:
                result = TestResult("test_429_rate_limiting", "PASS", duration, 
                                  "Rate limiting properly implemented (429 responses detected)")
            else:
                # Rate limiting might not be implemented, which is also okay
                result = TestResult("test_429_rate_limiting", "PASS", duration, 
                                  "No rate limiting detected (may not be implemented)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_429_rate_limiting", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_error_response_structure(self):
        """Test error response structure consistency"""
        start_time = time.time()
        
        try:
            # Generate various error responses
            error_tests = [
                ('GET', '/nonexistent'),  # 404
                ('POST', '/configurations'),  # 401 (no auth)
                ('PATCH', '/configurations'),  # 405 (method not allowed)
                ('POST', '/configurations', {'Content-Type': 'application/json'}, '{"invalid": json}'),  # 400
            ]
            
            consistent_errors = 0
            
            for test in error_tests:
                if len(test) == 4:
                    method, endpoint, headers, body = test
                    status, response, req_duration, resp_headers = await self._make_request(method, endpoint, headers, None, False, body)
                else:
                    method, endpoint = test
                    status, response, req_duration, resp_headers = await self._make_request(method, endpoint)
                
                # Check if error response has consistent structure
                if status >= 400 and isinstance(response, dict):
                    # Look for common error fields
                    has_error_field = 'error' in response or 'message' in response or 'errors' in response
                    if has_error_field:
                        consistent_errors += 1
                elif status >= 400 and isinstance(response, str):
                    # String responses are also acceptable
                    consistent_errors += 0.5
            
            duration = time.time() - start_time
            success_rate = (consistent_errors / len(error_tests)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_error_response_structure", "PASS", duration, 
                                  f"Error response structure consistent: {consistent_errors}/{len(error_tests)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_error_response_structure", "FAIL", duration, 
                                  f"Error response structure inconsistent: only {consistent_errors}/{len(error_tests)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_error_response_structure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_error_message_consistency(self):
        """Test error message consistency and helpfulness"""
        start_time = time.time()
        
        try:
            # Test that error messages are helpful and consistent
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations')
            
            duration = time.time() - start_time
            
            if status == 401 and isinstance(response, dict):
                error_message = response.get('error') or response.get('message') or str(response)
                
                # Check if error message is helpful
                helpful_keywords = ['unauthorized', 'authentication', 'token', 'login', 'access']
                is_helpful = any(keyword in error_message.lower() for keyword in helpful_keywords)
                
                if is_helpful:
                    result = TestResult("test_error_message_consistency", "PASS", duration, 
                                      f"Error message helpful: {error_message[:50]}...")
                else:
                    result = TestResult("test_error_message_consistency", "FAIL", duration, 
                                      f"Error message not helpful: {error_message[:50]}...")
            else:
                result = TestResult("test_error_message_consistency", "PASS", duration, 
                                  f"Error response received (status: {status})")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_error_message_consistency", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_error_codes_mapping(self):
        """Test that error codes map to appropriate HTTP status codes"""
        start_time = time.time()
        
        try:
            # Test various scenarios and their expected status codes
            status_tests = [
                ('GET', '/nonexistent', [404]),  # Not found
                ('POST', '/configurations', [401, 403]),  # Unauthorized
                ('INVALID_METHOD', '/configurations', [405]),  # Method not allowed
            ]
            
            correct_mappings = 0
            
            for method, endpoint, expected_statuses in status_tests:
                status, response, req_duration, resp_headers = await self._make_request(method, endpoint)
                
                if status in expected_statuses:
                    correct_mappings += 1
            
            duration = time.time() - start_time
            success_rate = (correct_mappings / len(status_tests)) * 100
            
            if success_rate >= 80:
                result = TestResult("test_error_codes_mapping", "PASS", duration, 
                                  f"Error code mapping correct: {correct_mappings}/{len(status_tests)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_error_codes_mapping", "FAIL", duration, 
                                  f"Error code mapping issues: only {correct_mappings}/{len(status_tests)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_error_codes_mapping", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_malformed_json(self):
        """Test handling of malformed JSON"""
        start_time = time.time()
        
        try:
            malformed_jsons = [
                '{"incomplete": ',
                '{"trailing": "comma",}',
                '{unquoted: "keys"}',
                '{"duplicate": "key", "duplicate": "value"}',
                '{"unicode": "\uFFFF"}',
                '{"nested": {"deep": {"very": {"extremely": {"deeply": {"nested": "value"}}}}}}' * 100,  # Very deep nesting
            ]
            
            proper_rejections = 0
            headers = {'Content-Type': 'application/json'}
            
            for malformed_json in malformed_jsons:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, None, False, malformed_json)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            success_rate = (proper_rejections / len(malformed_jsons)) * 100
            
            if success_rate >= 80:
                result = TestResult("test_malformed_json", "PASS", duration, 
                                  f"Malformed JSON handling good: {proper_rejections}/{len(malformed_jsons)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_malformed_json", "FAIL", duration, 
                                  f"Malformed JSON handling issues: only {proper_rejections}/{len(malformed_jsons)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_malformed_json", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_content_type(self):
        """Test handling of invalid Content-Type headers"""
        start_time = time.time()
        
        try:
            invalid_content_types = [
                '',  # Empty
                'invalid',  # Not a valid MIME type
                'application/',  # Incomplete
                'text/plain; charset=invalid',  # Invalid charset
                'application/json; boundary=something',  # Wrong parameter
                'APPLICATION/JSON',  # Case sensitivity
            ]
            
            handled_appropriately = 0
            
            for content_type in invalid_content_types:
                headers = {'Content-Type': content_type}
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, None, False, '{}')
                
                # Should either reject or handle gracefully
                if status in [400, 401, 403, 415]:
                    handled_appropriately += 1
            
            duration = time.time() - start_time
            success_rate = (handled_appropriately / len(invalid_content_types)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_invalid_content_type", "PASS", duration, 
                                  f"Invalid content-type handling good: {handled_appropriately}/{len(invalid_content_types)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_invalid_content_type", "FAIL", duration, 
                                  f"Invalid content-type handling issues: only {handled_appropriately}/{len(invalid_content_types)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_content_type", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_missing_required_headers(self):
        """Test handling of missing required headers"""
        start_time = time.time()
        
        try:
            # Test requests without common required headers
            header_tests = [
                {},  # No headers
                {'Content-Type': 'application/json'},  # No Origin
                {'Origin': 'http://example.com'},  # No Content-Type for POST
                {'Accept': 'application/json'},  # Missing other headers
            ]
            
            handled_gracefully = 0
            
            for headers in header_tests:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, {'test': 'data'})
                
                # Should handle missing headers gracefully
                if status in [200, 201, 400, 401, 403]:
                    handled_gracefully += 1
            
            duration = time.time() - start_time
            success_rate = (handled_gracefully / len(header_tests)) * 100
            
            if success_rate >= 80:
                result = TestResult("test_missing_required_headers", "PASS", duration, 
                                  f"Missing headers handled gracefully: {handled_gracefully}/{len(header_tests)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_missing_required_headers", "FAIL", duration, 
                                  f"Missing headers handling issues: only {handled_gracefully}/{len(header_tests)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_missing_required_headers", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_extremely_long_urls(self):
        """Test handling of extremely long URLs"""
        start_time = time.time()
        
        try:
            # Test various long URL scenarios
            long_urls = [
                '/configurations/' + 'x' * 1000,  # Very long ID
                '/rounds/' + 'a' * 2000,  # Even longer ID
                '/scores/' + '?' + '&'.join([f'param{i}=value{i}' for i in range(100)]),  # Many query params
                '/user/profile' + '?' + 'x' * 5000,  # Very long query string
            ]
            
            handled_appropriately = 0
            
            for url in long_urls:
                status, response, req_duration, resp_headers = await self._make_request('GET', url)
                
                # Should either reject or handle gracefully (not crash)
                if status in [400, 401, 403, 404, 414]:  # 414 = URI Too Long
                    handled_appropriately += 1
                elif status is None:  # Network level rejection is also acceptable
                    handled_appropriately += 0.5
            
            duration = time.time() - start_time
            success_rate = (handled_appropriately / len(long_urls)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_extremely_long_urls", "PASS", duration, 
                                  f"Long URL handling good: {handled_appropriately}/{len(long_urls)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_extremely_long_urls", "FAIL", duration, 
                                  f"Long URL handling issues: only {handled_appropriately}/{len(long_urls)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_extremely_long_urls", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_http_methods(self):
        """Test handling of invalid HTTP methods"""
        start_time = time.time()
        
        try:
            # Test completely invalid HTTP methods
            invalid_methods = [
                'INVALID',
                'HACK',
                'EXPLOIT',
                'TEST',
                '',  # Empty method
                'get',  # Lowercase (should be uppercase)
                'G E T',  # Spaces
                'GET/POST',  # Multiple methods
            ]
            
            handled_appropriately = 0
            
            for method in invalid_methods:
                try:
                    status, response, req_duration, resp_headers = await self._make_request(method, '/configurations')
                    
                    # Should reject invalid methods
                    if status in [400, 405, 501]:  # 501 = Not Implemented
                        handled_appropriately += 1
                except Exception:
                    # Exception at client level is also acceptable for invalid methods
                    handled_appropriately += 1
            
            duration = time.time() - start_time
            success_rate = (handled_appropriately / len(invalid_methods)) * 100
            
            if success_rate >= 70:
                result = TestResult("test_invalid_http_methods", "PASS", duration, 
                                  f"Invalid method handling good: {handled_appropriately}/{len(invalid_methods)} ({success_rate:.1f}%)")
            else:
                result = TestResult("test_invalid_http_methods", "FAIL", duration, 
                                  f"Invalid method handling issues: only {handled_appropriately}/{len(invalid_methods)} ({success_rate:.1f}%)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_http_methods", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)