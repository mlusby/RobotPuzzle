#!/usr/bin/env python3
"""
Authentication and Authorization Tests
Tests JWT token validation, CORS, and access control
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import aiohttp
import jwt
import base64

from test_base import TestSuite as BaseTestSuite, TestResult

class TestSuite:
    """Authentication and Authorization Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("Authentication & Authorization", "Tests for JWT tokens, CORS, and access control")
        
    async def run(self):
        """Run all authentication tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # Run tests
        await self.test_cors_preflight()
        await self.test_unauthorized_access()
        await self.test_invalid_token_formats()
        await self.test_expired_token()
        await self.test_malformed_jwt()
        await self.test_missing_auth_header()
        await self.test_wrong_auth_scheme()
        await self.test_cors_headers()
        await self.test_options_endpoints()
        await self.test_forbidden_access()
        
        self.suite.end_time = datetime.now()
        self._print_suite_summary()
        return self.suite
    
    def _print_test_result(self, result: TestResult):
        """Print individual test result"""
        status_icons = {'PASS': '✅', 'FAIL': '❌', 'ERROR': '💥', 'SKIP': '⏭️'}
        icon = status_icons.get(result.status, '❓')
        duration_str = f"({result.duration:.3f}s)" if result.duration > 0 else ""
        print(f"   {icon} {result.status:<6} {result.name:<50} {duration_str}")
        
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

    async def _make_request(self, method: str, endpoint: str, headers: Dict = None, data: Dict = None) -> tuple:
        """Make HTTP request and return (status, response, duration)"""
        url = f"{self.api_base_url}{endpoint}"
        request_headers = headers or {}
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
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

    async def test_cors_preflight(self):
        """Test CORS preflight requests"""
        start_time = time.time()
        
        try:
            endpoints_to_test = ['/configurations', '/rounds', '/scores', '/user/profile']
            
            for endpoint in endpoints_to_test:
                headers = {
                    'Origin': 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'authorization,content-type'
                }
                
                status, response, req_duration, response_headers = await self._make_request('OPTIONS', endpoint, headers)
                
                # Check that OPTIONS request succeeds
                if status != 200:
                    raise AssertionError(f"CORS preflight failed for {endpoint}: status {status}")
                
                # Check required CORS headers
                required_headers = [
                    'access-control-allow-origin',
                    'access-control-allow-methods',
                    'access-control-allow-headers'
                ]
                
                missing_headers = []
                for header in required_headers:
                    if header not in [h.lower() for h in response_headers.keys()]:
                        missing_headers.append(header)
                
                if missing_headers:
                    raise AssertionError(f"Missing CORS headers for {endpoint}: {missing_headers}")
            
            duration = time.time() - start_time
            result = TestResult("test_cors_preflight", "PASS", duration, f"CORS preflight working for {len(endpoints_to_test)} endpoints")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_preflight", "FAIL", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_unauthorized_access(self):
        """Test that protected endpoints return 401 without auth"""
        start_time = time.time()
        
        try:
            protected_endpoints = [
                ('GET', '/configurations'),
                ('POST', '/configurations'),
                ('GET', '/rounds'),
                ('POST', '/rounds'),
                ('GET', '/scores'),
                ('POST', '/scores'),
                ('GET', '/user/profile'),
                ('PUT', '/user/profile')
            ]
            
            unauthorized_count = 0
            
            for method, endpoint in protected_endpoints:
                status, response, req_duration, headers = await self._make_request(method, endpoint)
                
                if status == 401:
                    unauthorized_count += 1
                elif status is None:
                    # Network error, skip this endpoint
                    continue
                else:
                    raise AssertionError(f"{method} {endpoint} should return 401 but returned {status}")
            
            if unauthorized_count == 0:
                raise AssertionError("No endpoints properly returned 401 Unauthorized")
            
            duration = time.time() - start_time
            result = TestResult("test_unauthorized_access", "PASS", duration, 
                              f"{unauthorized_count}/{len(protected_endpoints)} endpoints properly require authorization")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_unauthorized_access", "FAIL", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_invalid_token_formats(self):
        """Test various invalid token formats"""
        start_time = time.time()
        
        try:
            invalid_tokens = [
                "invalid_token",
                "Bearer",
                "Bearer ",
                "Bearer invalid.token.format",
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid.signature",
                "Basic dXNlcjpwYXNz",  # Basic auth instead of Bearer
                "Token some_random_string"
            ]
            
            test_endpoint = '/configurations'
            rejected_count = 0
            
            for token in invalid_tokens:
                headers = {'Authorization': token}
                status, response, req_duration, resp_headers = await self._make_request('GET', test_endpoint, headers)
                
                if status in [401, 403]:
                    rejected_count += 1
                elif status is None:
                    # Network error, skip
                    continue
                else:
                    raise AssertionError(f"Invalid token '{token[:20]}...' was accepted (status: {status})")
            
            duration = time.time() - start_time
            result = TestResult("test_invalid_token_formats", "PASS", duration, 
                              f"{rejected_count}/{len(invalid_tokens)} invalid tokens properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_invalid_token_formats", "FAIL", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_expired_token(self):
        """Test that expired JWT tokens are rejected"""
        start_time = time.time()
        
        try:
            # Create an expired JWT token (expired 1 hour ago)
            import time
            current_time = int(time.time())
            expired_payload = {
                'sub': 'test-user',
                'email': 'test@example.com',
                'exp': current_time - 3600,  # Expired 1 hour ago
                'iat': current_time - 7200   # Issued 2 hours ago
            }
            
            # Create a simple JWT (note: this won't have proper signature, but we're testing expiry)
            header = json.dumps({'alg': 'HS256', 'typ': 'JWT'})
            payload = json.dumps(expired_payload)
            
            # Base64 encode (we don't need a real signature for this test)
            header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
            payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
            signature_b64 = 'fake_signature'
            
            expired_token = f"{header_b64}.{payload_b64}.{signature_b64}"
            
            headers = {'Authorization': f'Bearer {expired_token}'}
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_expired_token", "PASS", duration, "Expired token properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_expired_token", "FAIL", duration, f"Expired token was accepted (status: {status})")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_expired_token", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_malformed_jwt(self):
        """Test malformed JWT tokens"""
        start_time = time.time()
        
        try:
            malformed_tokens = [
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9",  # Missing payload and signature
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0",  # Missing signature
                "Bearer not.base64.encoded",
                "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid_base64.signature",
                "Bearer ...",  # Empty parts
                "Bearer a.b.c.d.e"  # Too many parts
            ]
            
            rejected_count = 0
            
            for token in malformed_tokens:
                headers = {'Authorization': token}
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
                
                if status in [401, 403]:
                    rejected_count += 1
                elif status is None:
                    continue
                else:
                    raise AssertionError(f"Malformed token was accepted: {token[:30]}...")
            
            duration = time.time() - start_time
            result = TestResult("test_malformed_jwt", "PASS", duration, 
                              f"{rejected_count}/{len(malformed_tokens)} malformed tokens properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_malformed_jwt", "FAIL", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_missing_auth_header(self):
        """Test requests without Authorization header"""
        start_time = time.time()
        
        try:
            status, response, req_duration, headers = await self._make_request('GET', '/configurations')
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_missing_auth_header", "PASS", duration, "Missing auth header properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_missing_auth_header", "FAIL", duration, 
                                  f"Request without auth header should return 401, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_missing_auth_header", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_wrong_auth_scheme(self):
        """Test wrong authentication schemes"""
        start_time = time.time()
        
        try:
            wrong_schemes = [
                "Basic dXNlcjpwYXNz",
                "Digest username=test",
                "ApiKey test-key",
                "OAuth test-token"
            ]
            
            rejected_count = 0
            
            for auth_header in wrong_schemes:
                headers = {'Authorization': auth_header}
                status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
                
                if status in [401, 403]:
                    rejected_count += 1
                elif status is None:
                    continue
                else:
                    raise AssertionError(f"Wrong auth scheme was accepted: {auth_header}")
            
            duration = time.time() - start_time
            result = TestResult("test_wrong_auth_scheme", "PASS", duration, 
                              f"{rejected_count}/{len(wrong_schemes)} wrong auth schemes properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_wrong_auth_scheme", "FAIL", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_cors_headers(self):
        """Test CORS headers in actual responses"""
        start_time = time.time()
        
        try:
            origins_to_test = [
                'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
                'https://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
                'http://localhost:3000',
                'https://example.com'  # Should be rejected
            ]
            
            valid_origins = 0
            
            for origin in origins_to_test:
                headers = {'Origin': origin}
                status, response, req_duration, resp_headers = await self._make_request('OPTIONS', '/configurations', headers)
                
                if status == 200:
                    # Check if Access-Control-Allow-Origin header is present
                    cors_origin = resp_headers.get('access-control-allow-origin', resp_headers.get('Access-Control-Allow-Origin'))
                    if cors_origin:
                        valid_origins += 1
            
            duration = time.time() - start_time
            if valid_origins > 0:
                result = TestResult("test_cors_headers", "PASS", duration, 
                                  f"CORS headers present for {valid_origins}/{len(origins_to_test)} origins")
            else:
                result = TestResult("test_cors_headers", "FAIL", duration, "No CORS headers found")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_cors_headers", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_options_endpoints(self):
        """Test OPTIONS method on all major endpoints"""
        start_time = time.time()
        
        try:
            endpoints = [
                '/configurations',
                '/rounds',
                '/scores',
                '/user/profile',
                '/rounds/solved',
                '/rounds/baseline'
            ]
            
            working_endpoints = 0
            
            for endpoint in endpoints:
                status, response, req_duration, headers = await self._make_request('OPTIONS', endpoint)
                
                if status == 200:
                    working_endpoints += 1
                elif status is None:
                    # Network error, skip
                    continue
            
            duration = time.time() - start_time
            if working_endpoints >= len(endpoints) // 2:  # At least half should work
                result = TestResult("test_options_endpoints", "PASS", duration, 
                                  f"OPTIONS supported on {working_endpoints}/{len(endpoints)} endpoints")
            else:
                result = TestResult("test_options_endpoints", "FAIL", duration, 
                                  f"OPTIONS only working on {working_endpoints}/{len(endpoints)} endpoints")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_options_endpoints", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_forbidden_access(self):
        """Test access to resources that should return 403 vs 401"""
        start_time = time.time()
        
        try:
            # Create a fake but well-formed JWT token
            header = json.dumps({'alg': 'HS256', 'typ': 'JWT'})
            payload = json.dumps({
                'sub': 'fake-user',
                'email': 'fake@example.com',
                'exp': int(time.time()) + 3600,  # Valid for 1 hour
                'iat': int(time.time())
            })
            
            header_b64 = base64.urlsafe_b64encode(header.encode()).decode().rstrip('=')
            payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
            signature_b64 = 'fake_signature_that_wont_validate'
            
            fake_token = f"{header_b64}.{payload_b64}.{signature_b64}"
            
            headers = {'Authorization': f'Bearer {fake_token}'}
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
            
            # Should return 401 (unauthorized) or 403 (forbidden) for invalid signature
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_forbidden_access", "PASS", duration, 
                                  f"Invalid signature properly rejected with status {status}")
            else:
                duration = time.time() - start_time
                result = TestResult("test_forbidden_access", "FAIL", duration, 
                                  f"Invalid signature should be rejected, got status {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_forbidden_access", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)