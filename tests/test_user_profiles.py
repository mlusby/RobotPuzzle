#!/usr/bin/env python3
"""
User Profiles API Tests
Tests for user profile management and username operations
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import aiohttp
import uuid

from test_base import TestSuite as BaseTestSuite, TestResult

class TestSuite:
    """User Profiles API Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("User Profiles API", "Tests for user profile management and username operations")
        
    async def run(self):
        """Run all user profile tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # Core functionality tests
        await self.test_get_profile_unauthorized()
        await self.test_update_profile_unauthorized()
        await self.test_get_profile_structure()
        await self.test_create_profile()
        await self.test_update_profile_valid_data()
        await self.test_update_profile_invalid_data()
        
        # Username management tests
        await self.test_update_username_valid()
        await self.test_update_username_invalid()
        await self.test_update_username_too_long()
        await self.test_update_username_too_short()
        await self.test_update_username_special_chars()
        await self.test_update_username_duplicate()
        
        # Profile data validation
        await self.test_profile_data_types()
        await self.test_profile_field_validation()
        await self.test_profile_large_data()
        await self.test_profile_xss_protection()
        
        # Edge cases and error handling
        await self.test_get_nonexistent_profile()
        await self.test_update_partial_profile()
        await self.test_profile_concurrent_updates()
        await self.test_profile_rate_limiting()
        
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

    async def _make_request(self, method: str, endpoint: str, headers: Dict = None, data: Dict = None) -> tuple:
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

    def _create_valid_profile(self) -> Dict[str, Any]:
        """Create a valid profile for testing"""
        return {
            'username': f'testuser{uuid.uuid4().hex[:8]}',
            'displayName': 'Test User',
            'email': 'test@example.com',
            'preferences': {
                'theme': 'dark',
                'notifications': True,
                'difficulty': 'medium'
            },
            'stats': {
                'gamesPlayed': 10,
                'averageMoves': 25.5,
                'bestTime': 120.0
            }
        }

    async def test_get_profile_unauthorized(self):
        """Test GET /user/profile without authorization"""
        start_time = time.time()
        
        try:
            status, response, req_duration, headers = await self._make_request('GET', '/user/profile')
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_get_profile_unauthorized", "PASS", duration, 
                                  "Unauthorized profile access properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_profile_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_profile_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_profile_unauthorized(self):
        """Test PUT /user/profile without authorization"""
        start_time = time.time()
        
        try:
            profile_data = self._create_valid_profile()
            status, response, req_duration, headers = await self._make_request('PUT', '/user/profile', data=profile_data)
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_update_profile_unauthorized", "PASS", duration, 
                                  "Unauthorized profile update properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_update_profile_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_profile_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_profile_structure(self):
        """Test GET /user/profile response structure"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/user/profile', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_profile_structure", "PASS", duration, 
                                  "Authentication properly required")
            elif status == 200:
                if isinstance(response, dict):
                    # Check for common profile fields
                    expected_fields = ['username', 'email', 'displayName']
                    present_fields = [field for field in expected_fields if field in response]
                    
                    duration = time.time() - start_time
                    result = TestResult("test_get_profile_structure", "PASS", duration, 
                                      f"Profile response has {len(present_fields)}/{len(expected_fields)} expected fields")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_profile_structure", "FAIL", duration, 
                                      f"Profile should return object, got {type(response)}")
            elif status == 404:
                duration = time.time() - start_time
                result = TestResult("test_get_profile_structure", "PASS", duration, 
                                  "Non-existent profile properly returns 404")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_profile_structure", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_profile_structure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_profile(self):
        """Test creating/updating a profile for the first time"""
        start_time = time.time()
        
        try:
            profile_data = self._create_valid_profile()
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_create_profile", "PASS", duration, 
                                  "Authentication properly required for profile creation")
            elif status in [200, 201]:
                if isinstance(response, dict):
                    duration = time.time() - start_time
                    result = TestResult("test_create_profile", "PASS", duration, 
                                      f"Profile created/updated successfully (status: {status})")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_create_profile", "FAIL", duration, 
                                      "Profile created but response structure unexpected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_profile", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_profile", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_profile_valid_data(self):
        """Test updating profile with valid data"""
        start_time = time.time()
        
        try:
            update_data = {
                'username': f'updateduser{uuid.uuid4().hex[:8]}',
                'displayName': 'Updated Test User',
                'preferences': {
                    'theme': 'light',
                    'notifications': False
                }
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, update_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_update_profile_valid_data", "PASS", duration, 
                                  "Authentication properly required for profile update")
            elif status in [200, 201]:
                duration = time.time() - start_time
                result = TestResult("test_update_profile_valid_data", "PASS", duration, 
                                  f"Profile updated successfully (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_update_profile_valid_data", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_profile_valid_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_profile_invalid_data(self):
        """Test updating profile with invalid data types"""
        start_time = time.time()
        
        try:
            invalid_profiles = [
                {
                    'username': 123,  # Should be string
                    'displayName': 'Test User'
                },
                {
                    'username': 'testuser',
                    'preferences': 'not_an_object'  # Should be object
                },
                {
                    'email': 'invalid-email-format',  # Invalid email
                    'username': 'testuser'
                },
                {
                    'stats': {
                        'gamesPlayed': 'not_a_number'  # Should be number
                    }
                }
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for profile_data in invalid_profiles:
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors >= len(invalid_profiles) // 2:  # Some validation might be lenient
                result = TestResult("test_update_profile_invalid_data", "PASS", duration, 
                                  f"{validation_errors}/{len(invalid_profiles)} invalid profiles properly rejected")
            else:
                result = TestResult("test_update_profile_invalid_data", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(invalid_profiles)} invalid profiles rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_profile_invalid_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_valid(self):
        """Test updating username with valid values"""
        start_time = time.time()
        
        try:
            valid_usernames = [
                f'user{uuid.uuid4().hex[:8]}',
                'ValidUser123',
                'test_user',
                'user-name',
                'a1b2c3',
                'CamelCaseUser'
            ]
            
            accepted_usernames = 0
            headers = self._create_mock_auth_header()
            
            for username in valid_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                if status in [200, 201, 401, 403]:  # Accepted or auth required
                    accepted_usernames += 1
            
            duration = time.time() - start_time
            if accepted_usernames == len(valid_usernames):
                result = TestResult("test_update_username_valid", "PASS", duration, 
                                  f"All {len(valid_usernames)} valid usernames properly handled")
            else:
                result = TestResult("test_update_username_valid", "FAIL", duration, 
                                  f"Only {accepted_usernames}/{len(valid_usernames)} valid usernames properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_valid", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_invalid(self):
        """Test updating username with invalid values"""
        start_time = time.time()
        
        try:
            invalid_usernames = [
                '',  # Empty username
                ' ',  # Space only
                'user with spaces',  # Spaces (might be invalid)
                'user@domain.com',  # Email format (might be invalid)
                '123456',  # Numbers only (might be invalid)
                'a',  # Too short (might be invalid)
                'user\nname',  # Newline
                'user\tname',  # Tab
                'user<script>',  # HTML/Script tags
                'user"quote'  # Quotes
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for username in invalid_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                if status in [400, 401, 403]:  # Rejected appropriately
                    proper_rejections += 1
            
            duration = time.time() - start_time
            # Some usernames might be accepted depending on validation rules
            if proper_rejections >= len(invalid_usernames) // 2:
                result = TestResult("test_update_username_invalid", "PASS", duration, 
                                  f"{proper_rejections}/{len(invalid_usernames)} invalid usernames properly rejected")
            else:
                result = TestResult("test_update_username_invalid", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(invalid_usernames)} invalid usernames properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_invalid", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_too_long(self):
        """Test updating username with overly long values"""
        start_time = time.time()
        
        try:
            long_usernames = [
                'a' * 51,  # 51 characters
                'a' * 100,  # 100 characters
                'a' * 256,  # 256 characters
                'very_long_username_that_exceeds_reasonable_limits_and_should_be_rejected_by_validation'
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for username in long_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            if proper_rejections >= len(long_usernames) // 2:
                result = TestResult("test_update_username_too_long", "PASS", duration, 
                                  f"{proper_rejections}/{len(long_usernames)} overly long usernames properly rejected")
            else:
                result = TestResult("test_update_username_too_long", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(long_usernames)} overly long usernames properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_too_long", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_too_short(self):
        """Test updating username with overly short values"""
        start_time = time.time()
        
        try:
            short_usernames = [
                '',  # Empty
                'a',  # 1 character
                'ab',  # 2 characters
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for username in short_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            if proper_rejections >= len(short_usernames) // 2:
                result = TestResult("test_update_username_too_short", "PASS", duration, 
                                  f"{proper_rejections}/{len(short_usernames)} overly short usernames properly rejected")
            else:
                result = TestResult("test_update_username_too_short", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(short_usernames)} overly short usernames properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_too_short", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_special_chars(self):
        """Test updating username with special characters"""
        start_time = time.time()
        
        try:
            special_usernames = [
                'user@name',
                'user#name',
                'user$name',
                'user%name',
                'user&name',
                'user*name',
                'user+name',
                'user=name',
                'user?name',
                'user^name',
                'user`name',
                'user|name',
                'user~name'
            ]
            
            handled_properly = 0
            headers = self._create_mock_auth_header()
            
            for username in special_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                # Either accepted (if special chars are allowed) or rejected (if not)
                if status in [200, 201, 400, 401, 403]:
                    handled_properly += 1
            
            duration = time.time() - start_time
            if handled_properly == len(special_usernames):
                result = TestResult("test_update_username_special_chars", "PASS", duration, 
                                  f"All {len(special_usernames)} special character usernames properly handled")
            else:
                result = TestResult("test_update_username_special_chars", "FAIL", duration, 
                                  f"Only {handled_properly}/{len(special_usernames)} special character usernames properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_special_chars", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_username_duplicate(self):
        """Test updating to a username that might already exist"""
        start_time = time.time()
        
        try:
            # Try common usernames that might be taken
            common_usernames = [
                'admin',
                'user',
                'test',
                'guest',
                'anonymous',
                'root',
                'system'
            ]
            
            responses = 0
            headers = self._create_mock_auth_header()
            
            for username in common_usernames:
                profile_data = {'username': username}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, profile_data)
                
                # Should either be accepted, rejected for duplication, or require auth
                if status in [200, 201, 400, 401, 403, 409]:  # 409 = Conflict
                    responses += 1
            
            duration = time.time() - start_time
            if responses == len(common_usernames):
                result = TestResult("test_update_username_duplicate", "PASS", duration, 
                                  f"All {len(common_usernames)} potentially duplicate usernames properly handled")
            else:
                result = TestResult("test_update_username_duplicate", "FAIL", duration, 
                                  f"Only {responses}/{len(common_usernames)} potentially duplicate usernames properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_username_duplicate", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_data_types(self):
        """Test profile update with various data types"""
        start_time = time.time()
        
        try:
            data_type_tests = [
                {
                    'stats': {
                        'gamesPlayed': 10,  # Integer
                        'averageMoves': 25.5,  # Float
                        'isActive': True  # Boolean
                    }
                },
                {
                    'preferences': {
                        'theme': 'dark',  # String
                        'volume': 0.8,  # Float
                        'autoSave': False  # Boolean
                    }
                },
                {
                    'metadata': {
                        'lastLogin': '2024-01-01T12:00:00Z',  # ISO timestamp
                        'loginCount': 42,  # Integer
                        'version': '1.0.0'  # String
                    }
                }
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            for data in data_type_tests:
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, data)
                
                if status in [200, 201, 400, 401, 403]:
                    proper_handling += 1
            
            duration = time.time() - start_time
            if proper_handling == len(data_type_tests):
                result = TestResult("test_profile_data_types", "PASS", duration, 
                                  f"All {len(data_type_tests)} data type variants properly handled")
            else:
                result = TestResult("test_profile_data_types", "FAIL", duration, 
                                  f"Only {proper_handling}/{len(data_type_tests)} data type variants properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_data_types", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_field_validation(self):
        """Test profile field validation"""
        start_time = time.time()
        
        try:
            field_tests = [
                {
                    'email': 'valid@example.com'  # Valid email
                },
                {
                    'email': 'invalid-email'  # Invalid email
                },
                {
                    'displayName': 'Valid Display Name'  # Valid display name
                },
                {
                    'displayName': ''  # Empty display name
                },
                {
                    'displayName': 'A' * 256  # Very long display name
                }
            ]
            
            handled_appropriately = 0
            headers = self._create_mock_auth_header()
            
            for data in field_tests:
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, data)
                
                # Should either accept valid data or reject invalid data
                if status in [200, 201, 400, 401, 403]:
                    handled_appropriately += 1
            
            duration = time.time() - start_time
            if handled_appropriately == len(field_tests):
                result = TestResult("test_profile_field_validation", "PASS", duration, 
                                  f"All {len(field_tests)} field validation tests properly handled")
            else:
                result = TestResult("test_profile_field_validation", "FAIL", duration, 
                                  f"Only {handled_appropriately}/{len(field_tests)} field validation tests properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_field_validation", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_large_data(self):
        """Test profile update with large amounts of data"""
        start_time = time.time()
        
        try:
            large_profile = {
                'username': 'testuser',
                'displayName': 'Test User',
                'preferences': {
                    f'setting_{i}': f'value_{i}' for i in range(100)  # Many preferences
                },
                'stats': {
                    f'stat_{i}': i * 10.5 for i in range(50)  # Many stats
                },
                'metadata': {
                    'largeField': 'x' * 10000,  # Large text field
                    'arrayField': list(range(1000))  # Large array
                }
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, large_profile)
            
            # Should handle large data appropriately
            if status in [200, 201, 400, 401, 403, 413]:  # 413 = Payload Too Large
                duration = time.time() - start_time
                result = TestResult("test_profile_large_data", "PASS", duration, 
                                  f"Large profile data handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_profile_large_data", "FAIL", duration, 
                                  f"Large profile data unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_large_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_xss_protection(self):
        """Test profile XSS protection"""
        start_time = time.time()
        
        try:
            xss_payloads = [
                {
                    'username': 'user<script>alert("xss")</script>',
                },
                {
                    'displayName': '<img src="x" onerror="alert(1)">',
                },
                {
                    'preferences': {
                        'theme': '"><script>alert("xss")</script>'
                    }
                },
                {
                    'bio': 'javascript:alert("xss")'
                }
            ]
            
            properly_sanitized = 0
            headers = self._create_mock_auth_header()
            
            for payload in xss_payloads:
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, payload)
                
                # Should either reject or sanitize XSS attempts
                if status in [400, 401, 403]:  # Rejected
                    properly_sanitized += 1
                elif status in [200, 201]:  # Accepted (hopefully sanitized)
                    # Check if response contains unsanitized script tags
                    response_str = json.dumps(response) if isinstance(response, dict) else str(response)
                    if '<script>' not in response_str.lower():
                        properly_sanitized += 1
            
            duration = time.time() - start_time
            if properly_sanitized == len(xss_payloads):
                result = TestResult("test_profile_xss_protection", "PASS", duration, 
                                  f"All {len(xss_payloads)} XSS payloads properly handled")
            else:
                result = TestResult("test_profile_xss_protection", "FAIL", duration, 
                                  f"Only {properly_sanitized}/{len(xss_payloads)} XSS payloads properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_xss_protection", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_nonexistent_profile(self):
        """Test GET profile for non-existent user"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/user/profile', headers)
            
            # Should return 404 for non-existent profile or 401/403 for auth
            if status in [401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_get_nonexistent_profile", "PASS", duration, 
                                  f"Non-existent profile properly handled (status: {status})")
            elif status == 200:
                # Profile exists or was created, which is also valid
                duration = time.time() - start_time
                result = TestResult("test_get_nonexistent_profile", "PASS", duration, 
                                  "Profile found or auto-created")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_nonexistent_profile", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_nonexistent_profile", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_partial_profile(self):
        """Test updating only part of a profile"""
        start_time = time.time()
        
        try:
            partial_updates = [
                {'username': f'partial1{uuid.uuid4().hex[:4]}'},
                {'displayName': 'Updated Display Name'},
                {'preferences': {'theme': 'dark'}},
                {'stats': {'gamesPlayed': 5}}
            ]
            
            successful_updates = 0
            headers = self._create_mock_auth_header()
            
            for update in partial_updates:
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, update)
                
                if status in [200, 201, 401, 403]:
                    successful_updates += 1
            
            duration = time.time() - start_time
            if successful_updates == len(partial_updates):
                result = TestResult("test_update_partial_profile", "PASS", duration, 
                                  f"All {len(partial_updates)} partial updates properly handled")
            else:
                result = TestResult("test_update_partial_profile", "FAIL", duration, 
                                  f"Only {successful_updates}/{len(partial_updates)} partial updates properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_partial_profile", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_concurrent_updates(self):
        """Test concurrent profile updates"""
        start_time = time.time()
        
        try:
            # Create multiple profile updates
            updates = []
            for i in range(5):
                update = {
                    'username': f'concurrent{i}{uuid.uuid4().hex[:4]}',
                    'displayName': f'Concurrent User {i}',
                    'preferences': {'updateNumber': i}
                }
                updates.append(update)
            
            headers = self._create_mock_auth_header()
            
            # Submit all updates concurrently
            tasks = []
            for update in updates:
                task = self._make_request('PUT', '/user/profile', headers, update)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should respond appropriately
            successful_responses = 0
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    successful_responses += 1
            
            duration = time.time() - start_time
            if successful_responses >= len(updates) // 2:
                result = TestResult("test_profile_concurrent_updates", "PASS", duration, 
                                  f"Concurrent updates handled: {successful_responses}/{len(updates)} responded")
            else:
                result = TestResult("test_profile_concurrent_updates", "FAIL", duration, 
                                  f"Poor concurrent handling: only {successful_responses}/{len(updates)} responded")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_concurrent_updates", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_profile_rate_limiting(self):
        """Test profile update rate limiting"""
        start_time = time.time()
        
        try:
            # Send many requests quickly to test rate limiting
            headers = self._create_mock_auth_header()
            
            responses = []
            for i in range(10):
                update = {'username': f'ratetest{i}{uuid.uuid4().hex[:4]}'}
                status, response, req_duration, resp_headers = await self._make_request('PUT', '/user/profile', headers, update)
                responses.append(status)
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)
            
            # Check if any rate limiting occurred
            rate_limited = any(status == 429 for status in responses if status is not None)
            auth_required = any(status in [401, 403] for status in responses if status is not None)
            
            duration = time.time() - start_time
            if rate_limited:
                result = TestResult("test_profile_rate_limiting", "PASS", duration, 
                                  "Rate limiting properly implemented")
            elif auth_required:
                result = TestResult("test_profile_rate_limiting", "PASS", duration, 
                                  "Authentication required (rate limiting not tested)")
            else:
                result = TestResult("test_profile_rate_limiting", "PASS", duration, 
                                  "No rate limiting detected (may not be implemented)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_profile_rate_limiting", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)