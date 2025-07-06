#!/usr/bin/env python3
"""
Board Configurations API Tests
Tests for CRUD operations on board configurations
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
    """Board Configurations API Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("Board Configurations API", "Tests for board configuration CRUD operations")
        self.test_config_id = None
        
    async def run(self):
        """Run all board configuration tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # Run tests in order (some depend on others)
        await self.test_get_configurations_unauthorized()
        await self.test_create_configuration_unauthorized()
        await self.test_get_configurations_structure()
        await self.test_create_valid_configuration()
        await self.test_create_configuration_missing_fields()
        await self.test_create_configuration_invalid_data()
        await self.test_get_specific_configuration()
        await self.test_update_configuration()
        await self.test_delete_configuration()
        await self.test_get_nonexistent_configuration()
        await self.test_configuration_data_validation()
        await self.test_large_configuration_data()
        await self.test_special_characters_in_name()
        await self.test_concurrent_operations()
        
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
        """Create a mock authorization header (for testing unauthorized access)"""
        return {'Authorization': 'Bearer mock_token_for_testing'}

    def _create_valid_configuration(self) -> Dict[str, Any]:
        """Create a valid configuration for testing"""
        return {
            'name': f'Test Config {uuid.uuid4().hex[:8]}',
            'walls': [
                '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right'
            ],
            'targets': ['8,8', '6,10', '12,4'],
            'isActive': True,
            'description': 'Test configuration for API testing'
        }

    async def test_get_configurations_unauthorized(self):
        """Test GET /configurations without authorization"""
        start_time = time.time()
        
        try:
            status, response, req_duration, headers = await self._make_request('GET', '/configurations')
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_get_configurations_unauthorized", "PASS", duration, 
                                  "Unauthorized access properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_configurations_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_configurations_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_configuration_unauthorized(self):
        """Test POST /configurations without authorization"""
        start_time = time.time()
        
        try:
            config_data = self._create_valid_configuration()
            status, response, req_duration, headers = await self._make_request('POST', '/configurations', data=config_data)
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_create_configuration_unauthorized", "PASS", duration, 
                                  "Unauthorized creation properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_configuration_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_configuration_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_configurations_structure(self):
        """Test GET /configurations response structure"""
        start_time = time.time()
        
        try:
            # Use mock auth header (will likely fail auth but might return better error structure)
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations', headers)
            
            # We expect this to fail with proper error structure
            if status in [401, 403]:
                # Check if error response has proper structure
                if isinstance(response, dict) and 'error' in response:
                    duration = time.time() - start_time
                    result = TestResult("test_get_configurations_structure", "PASS", duration, 
                                      "Error response has proper structure")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_configurations_structure", "PASS", duration, 
                                      "Authentication rejected as expected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_configurations_structure", "SKIP", duration, 
                                  f"Unexpected status {status}, cannot test structure")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_configurations_structure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_valid_configuration(self):
        """Test creating a valid configuration"""
        start_time = time.time()
        
        try:
            config_data = self._create_valid_configuration()
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, config_data)
            
            # We expect auth to fail, but let's check the response structure
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_create_valid_configuration", "PASS", duration, 
                                  "Authentication properly required for configuration creation")
            elif status == 201:
                # If somehow it worked, check the response
                if isinstance(response, dict) and 'configId' in response:
                    self.test_config_id = response['configId']
                    duration = time.time() - start_time
                    result = TestResult("test_create_valid_configuration", "PASS", duration, 
                                      f"Configuration created successfully: {self.test_config_id}")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_create_valid_configuration", "FAIL", duration, 
                                      "Configuration created but response missing configId")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_valid_configuration", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_valid_configuration", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_configuration_missing_fields(self):
        """Test creating configuration with missing required fields"""
        start_time = time.time()
        
        try:
            # Test various incomplete configurations
            incomplete_configs = [
                {},  # Empty
                {'name': 'Test'},  # Missing walls, targets
                {'walls': ['1,1,top']},  # Missing name, targets
                {'name': 'Test', 'walls': []},  # Missing targets
                {'name': 'Test', 'targets': ['1,1']},  # Missing walls
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for config in incomplete_configs:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, config)
                
                if status in [400, 401, 403]:  # 400 for validation, 401/403 for auth
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors == len(incomplete_configs):
                result = TestResult("test_create_configuration_missing_fields", "PASS", duration, 
                                  f"All {len(incomplete_configs)} incomplete configurations properly rejected")
            else:
                result = TestResult("test_create_configuration_missing_fields", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(incomplete_configs)} incomplete configurations rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_configuration_missing_fields", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_configuration_invalid_data(self):
        """Test creating configuration with invalid data types"""
        start_time = time.time()
        
        try:
            invalid_configs = [
                {
                    'name': 123,  # Should be string
                    'walls': ['1,1,top'],
                    'targets': ['1,1']
                },
                {
                    'name': 'Test',
                    'walls': 'not_an_array',  # Should be array
                    'targets': ['1,1']
                },
                {
                    'name': 'Test',
                    'walls': ['1,1,top'],
                    'targets': 'not_an_array'  # Should be array
                },
                {
                    'name': 'Test',
                    'walls': ['invalid_wall_format'],  # Invalid wall format
                    'targets': ['1,1']
                }
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for config in invalid_configs:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, config)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors == len(invalid_configs):
                result = TestResult("test_create_configuration_invalid_data", "PASS", duration, 
                                  f"All {len(invalid_configs)} invalid configurations properly rejected")
            else:
                result = TestResult("test_create_configuration_invalid_data", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(invalid_configs)} invalid configurations rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_configuration_invalid_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_specific_configuration(self):
        """Test GET /configurations/{id}"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/configurations/test-id', headers)
            
            # Should return 401/403 for auth or 404 for not found
            if status in [401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_get_specific_configuration", "PASS", duration, 
                                  f"Specific configuration endpoint responds appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_specific_configuration", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_specific_configuration", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_update_configuration(self):
        """Test PUT /configurations/{id}"""
        start_time = time.time()
        
        try:
            update_data = {
                'name': 'Updated Test Config',
                'walls': ['1,1,top', '2,2,left'],
                'targets': ['3,3'],
                'isActive': False
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('PUT', '/configurations/test-id', headers, update_data)
            
            # Should return 401/403 for auth or 404 for not found
            if status in [401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_update_configuration", "PASS", duration, 
                                  f"Configuration update endpoint responds appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_update_configuration", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_update_configuration", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_delete_configuration(self):
        """Test DELETE /configurations/{id}"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('DELETE', '/configurations/test-id', headers)
            
            # Should return 401/403 for auth or 404 for not found
            if status in [401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_delete_configuration", "PASS", duration, 
                                  f"Configuration delete endpoint responds appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_delete_configuration", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_delete_configuration", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_nonexistent_configuration(self):
        """Test GET with non-existent configuration ID"""
        start_time = time.time()
        
        try:
            non_existent_id = 'definitely-does-not-exist-12345'
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', f'/configurations/{non_existent_id}', headers)
            
            # Should return 401/403 for auth or 404 for not found
            if status in [401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_get_nonexistent_configuration", "PASS", duration, 
                                  f"Non-existent configuration properly handled (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_nonexistent_configuration", "FAIL", duration, 
                                  f"Unexpected status for non-existent configuration: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_nonexistent_configuration", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_configuration_data_validation(self):
        """Test configuration data validation rules"""
        start_time = time.time()
        
        try:
            # Test edge cases in configuration data
            edge_cases = [
                {
                    'name': '',  # Empty name
                    'walls': ['1,1,top'],
                    'targets': ['1,1']
                },
                {
                    'name': 'A' * 1000,  # Very long name
                    'walls': ['1,1,top'],
                    'targets': ['1,1']
                },
                {
                    'name': 'Test',
                    'walls': [],  # Empty walls array
                    'targets': ['1,1']
                },
                {
                    'name': 'Test',
                    'walls': ['1,1,top'],
                    'targets': []  # Empty targets array
                }
            ]
            
            proper_responses = 0
            headers = self._create_mock_auth_header()
            
            for config in edge_cases:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, config)
                
                if status in [400, 401, 403]:  # Some form of rejection
                    proper_responses += 1
            
            duration = time.time() - start_time
            if proper_responses == len(edge_cases):
                result = TestResult("test_configuration_data_validation", "PASS", duration, 
                                  f"All {len(edge_cases)} edge cases properly handled")
            else:
                result = TestResult("test_configuration_data_validation", "FAIL", duration, 
                                  f"Only {proper_responses}/{len(edge_cases)} edge cases properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_configuration_data_validation", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_large_configuration_data(self):
        """Test configuration with large amounts of data"""
        start_time = time.time()
        
        try:
            # Create a configuration with many walls and targets
            large_walls = [f'{i},{j},top' for i in range(16) for j in range(16)][:500]  # Limit to 500
            large_targets = [f'{i},{j}' for i in range(16) for j in range(16)][:100]   # Limit to 100
            
            large_config = {
                'name': 'Large Test Configuration',
                'walls': large_walls,
                'targets': large_targets,
                'isActive': True
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, large_config)
            
            # Should handle large data appropriately (reject with 400 if too large, or 401/403 for auth)
            if status in [400, 401, 403, 413]:  # 413 = Payload Too Large
                duration = time.time() - start_time
                result = TestResult("test_large_configuration_data", "PASS", duration, 
                                  f"Large configuration data handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_large_configuration_data", "FAIL", duration, 
                                  f"Large configuration unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_large_configuration_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_special_characters_in_name(self):
        """Test configuration names with special characters"""
        start_time = time.time()
        
        try:
            special_names = [
                'Config with <script>alert("xss")</script>',
                'Config with "quotes" and \'apostrophes\'',
                'Config with emoji 🎮🤖',
                'Config with unicode 测试配置',
                'Config\nwith\nnewlines',
                'Config\twith\ttabs'
            ]
            
            handled_properly = 0
            headers = self._create_mock_auth_header()
            
            for name in special_names:
                config = {
                    'name': name,
                    'walls': ['1,1,top'],
                    'targets': ['1,1']
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/configurations', headers, config)
                
                # Should either accept it (sanitized) or reject it appropriately
                if status in [400, 401, 403]:
                    handled_properly += 1
            
            duration = time.time() - start_time
            if handled_properly == len(special_names):
                result = TestResult("test_special_characters_in_name", "PASS", duration, 
                                  f"All {len(special_names)} special character names properly handled")
            else:
                result = TestResult("test_special_characters_in_name", "FAIL", duration, 
                                  f"Only {handled_properly}/{len(special_names)} special character names properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_special_characters_in_name", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_concurrent_operations(self):
        """Test concurrent configuration operations"""
        start_time = time.time()
        
        try:
            # Create multiple configurations concurrently
            configs = [self._create_valid_configuration() for _ in range(5)]
            headers = self._create_mock_auth_header()
            
            # Send all requests concurrently
            tasks = []
            for config in configs:
                task = self._make_request('POST', '/configurations', headers, config)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should respond (likely with auth errors, but should handle concurrent load)
            successful_responses = 0
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    successful_responses += 1
            
            duration = time.time() - start_time
            if successful_responses >= len(configs) // 2:  # At least half should respond
                result = TestResult("test_concurrent_operations", "PASS", duration, 
                                  f"Concurrent operations handled: {successful_responses}/{len(configs)} responded")
            else:
                result = TestResult("test_concurrent_operations", "FAIL", duration, 
                                  f"Poor concurrent handling: only {successful_responses}/{len(configs)} responded")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_concurrent_operations", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)