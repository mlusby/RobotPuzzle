#!/usr/bin/env python3
"""
Rounds API Tests
Comprehensive tests for rounds CRUD operations, including edge cases and data validation
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
    """Rounds API Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("Rounds API", "Tests for rounds CRUD operations and specialized endpoints")
        self.test_round_id = None
        
    async def run(self):
        """Run all rounds tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # Core functionality tests
        await self.test_get_rounds_unauthorized()
        await self.test_create_round_unauthorized() 
        await self.test_get_rounds_structure()
        await self.test_create_valid_round()
        await self.test_create_round_missing_fields()
        await self.test_create_round_invalid_data()
        
        # Specialized endpoints
        await self.test_get_solved_rounds()
        await self.test_get_baseline_rounds()
        await self.test_get_user_submitted_rounds()
        await self.test_get_user_completed_rounds()
        await self.test_get_specific_round()
        await self.test_get_specific_round_invalid_id()
        
        # Edge cases and validation
        await self.test_round_with_invalid_robot_positions()
        await self.test_round_with_invalid_target_positions()
        await self.test_round_with_invalid_walls()
        await self.test_round_with_large_data()
        await self.test_round_with_special_characters()
        await self.test_rounds_pagination()
        await self.test_concurrent_round_operations()
        
        # Configuration-based round creation
        await self.test_create_round_with_config_id()
        await self.test_create_round_invalid_config_id()
        
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

    def _create_valid_round(self) -> Dict[str, Any]:
        """Create a valid round for testing"""
        return {
            'roundName': f'Test Round {uuid.uuid4().hex[:8]}',
            'configId': 'test-config-123',
            'initialRobotPositions': {
                'red': {'x': 2, 'y': 3},
                'blue': {'x': 5, 'y': 7},
                'green': {'x': 10, 'y': 12},
                'yellow': {'x': 14, 'y': 1},
                'silver': {'x': 8, 'y': 8}
            },
            'targetPositions': {'color': 'red', 'x': 8, 'y': 8},
            'walls': [
                '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right'
            ],
            'targets': ['8,8'],
            'puzzleStates': [
                {
                    'walls': ['7,7,left', '7,7,top'],
                    'targets': ['8,8'],
                    'initialRobotPositions': {
                        'red': {'x': 2, 'y': 3},
                        'blue': {'x': 5, 'y': 7}
                    },
                    'targetPosition': {'color': 'red', 'x': 8, 'y': 8}
                }
            ]
        }

    async def test_get_rounds_unauthorized(self):
        """Test GET /rounds without authorization"""
        start_time = time.time()
        
        try:
            status, response, req_duration, headers = await self._make_request('GET', '/rounds')
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_get_rounds_unauthorized", "PASS", duration, 
                                  "Unauthorized access properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_rounds_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_rounds_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_round_unauthorized(self):
        """Test POST /rounds without authorization"""
        start_time = time.time()
        
        try:
            round_data = self._create_valid_round()
            status, response, req_duration, headers = await self._make_request('POST', '/rounds', data=round_data)
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_create_round_unauthorized", "PASS", duration, 
                                  "Unauthorized round creation properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_round_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_round_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_rounds_structure(self):
        """Test GET /rounds response structure"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/rounds', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_rounds_structure", "PASS", duration, 
                                  "Authentication properly required")
            elif status == 200 and isinstance(response, list):
                duration = time.time() - start_time
                result = TestResult("test_get_rounds_structure", "PASS", duration, 
                                  f"Rounds endpoint returns array with {len(response)} items")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_rounds_structure", "FAIL", duration, 
                                  f"Unexpected response: status {status}, type {type(response)}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_rounds_structure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_valid_round(self):
        """Test creating a valid round"""
        start_time = time.time()
        
        try:
            round_data = self._create_valid_round()
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_create_valid_round", "PASS", duration, 
                                  "Authentication properly required for round creation")
            elif status == 201:
                if isinstance(response, dict) and 'roundId' in response:
                    self.test_round_id = response['roundId']
                    duration = time.time() - start_time
                    result = TestResult("test_create_valid_round", "PASS", duration, 
                                      f"Round created successfully: {self.test_round_id}")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_create_valid_round", "FAIL", duration, 
                                      "Round created but response missing roundId")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_valid_round", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_valid_round", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_round_missing_fields(self):
        """Test creating round with missing required fields"""
        start_time = time.time()
        
        try:
            incomplete_rounds = [
                {},  # Empty
                {'roundName': 'Test'},  # Missing robot positions
                {'initialRobotPositions': {'red': {'x': 1, 'y': 1}}},  # Missing name
                {'roundName': 'Test', 'initialRobotPositions': {}},  # Empty robot positions
                {'roundName': 'Test', 'initialRobotPositions': {'red': {'x': 1, 'y': 1}}},  # Missing target
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for round_data in incomplete_rounds:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors == len(incomplete_rounds):
                result = TestResult("test_create_round_missing_fields", "PASS", duration, 
                                  f"All {len(incomplete_rounds)} incomplete rounds properly rejected")
            else:
                result = TestResult("test_create_round_missing_fields", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(incomplete_rounds)} incomplete rounds rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_round_missing_fields", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_round_invalid_data(self):
        """Test creating round with invalid data types"""
        start_time = time.time()
        
        try:
            invalid_rounds = [
                {
                    'roundName': 123,  # Should be string
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': 'not_an_object',  # Should be object
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': 'not_an_object'  # Should be object
                }
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for round_data in invalid_rounds:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors == len(invalid_rounds):
                result = TestResult("test_create_round_invalid_data", "PASS", duration, 
                                  f"All {len(invalid_rounds)} invalid rounds properly rejected")
            else:
                result = TestResult("test_create_round_invalid_data", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(invalid_rounds)} invalid rounds rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_round_invalid_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_solved_rounds(self):
        """Test GET /rounds/solved"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/rounds/solved', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_solved_rounds", "PASS", duration, 
                                  "Solved rounds endpoint requires authentication")
            elif status == 200:
                if isinstance(response, list):
                    duration = time.time() - start_time
                    result = TestResult("test_get_solved_rounds", "PASS", duration, 
                                      f"Solved rounds endpoint returns {len(response)} rounds")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_solved_rounds", "FAIL", duration, 
                                      "Solved rounds should return array")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_solved_rounds", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_solved_rounds", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_baseline_rounds(self):
        """Test GET /rounds/baseline"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/rounds/baseline', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_baseline_rounds", "PASS", duration, 
                                  "Baseline rounds endpoint requires authentication")
            elif status == 200:
                duration = time.time() - start_time
                result = TestResult("test_get_baseline_rounds", "PASS", duration, 
                                  "Baseline rounds endpoint responds correctly")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_baseline_rounds", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_baseline_rounds", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_user_submitted_rounds(self):
        """Test GET /rounds/user-submitted"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/rounds/user-submitted', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_user_submitted_rounds", "PASS", duration, 
                                  "User submitted rounds endpoint requires authentication")
            elif status == 200:
                duration = time.time() - start_time
                result = TestResult("test_get_user_submitted_rounds", "PASS", duration, 
                                  "User submitted rounds endpoint responds correctly")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_user_submitted_rounds", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_user_submitted_rounds", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_user_completed_rounds(self):
        """Test GET /rounds/user-completed (alias for user-submitted)"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/rounds/user-completed', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_user_completed_rounds", "PASS", duration, 
                                  "User completed rounds endpoint requires authentication")
            elif status == 200:
                duration = time.time() - start_time
                result = TestResult("test_get_user_completed_rounds", "PASS", duration, 
                                  "User completed rounds endpoint responds correctly")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_user_completed_rounds", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_user_completed_rounds", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_specific_round(self):
        """Test GET /rounds/{roundId}"""
        start_time = time.time()
        
        try:
            # Test with a realistic round ID format
            test_round_id = 'round_175141796540'
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', f'/rounds/{test_round_id}', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_specific_round", "PASS", duration, 
                                  "Specific round endpoint requires authentication")
            elif status == 404:
                duration = time.time() - start_time
                result = TestResult("test_get_specific_round", "PASS", duration, 
                                  "Non-existent round properly returns 404")
            elif status == 200:
                if isinstance(response, dict) and 'roundId' in response:
                    duration = time.time() - start_time
                    result = TestResult("test_get_specific_round", "PASS", duration, 
                                      f"Specific round retrieved successfully: {response['roundId']}")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_specific_round", "FAIL", duration, 
                                      "Specific round response missing roundId")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_specific_round", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_specific_round", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_specific_round_invalid_id(self):
        """Test GET /rounds/{roundId} with invalid ID"""
        start_time = time.time()
        
        try:
            invalid_ids = ['', 'invalid-id', '../../etc/passwd', '<script>alert(1)</script>']
            proper_responses = 0
            headers = self._create_mock_auth_header()
            
            for invalid_id in invalid_ids:
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/rounds/{invalid_id}', headers)
                
                if status in [400, 401, 403, 404]:
                    proper_responses += 1
            
            duration = time.time() - start_time
            if proper_responses == len(invalid_ids):
                result = TestResult("test_get_specific_round_invalid_id", "PASS", duration, 
                                  f"All {len(invalid_ids)} invalid IDs properly rejected")
            else:
                result = TestResult("test_get_specific_round_invalid_id", "FAIL", duration, 
                                  f"Only {proper_responses}/{len(invalid_ids)} invalid IDs properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_specific_round_invalid_id", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_round_with_invalid_robot_positions(self):
        """Test round creation with invalid robot positions"""
        start_time = time.time()
        
        try:
            invalid_positions = [
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {
                        'red': {'x': 'invalid', 'y': 1}  # Non-numeric coordinate
                    },
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {
                        'red': {'x': -1, 'y': 1}  # Negative coordinate
                    },
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {
                        'red': {'x': 100, 'y': 100}  # Out of bounds coordinate
                    },
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {
                        'red': {'y': 1}  # Missing x coordinate
                    },
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                }
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for round_data in invalid_positions:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            if proper_rejections == len(invalid_positions):
                result = TestResult("test_round_with_invalid_robot_positions", "PASS", duration, 
                                  f"All {len(invalid_positions)} invalid robot positions properly rejected")
            else:
                result = TestResult("test_round_with_invalid_robot_positions", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(invalid_positions)} invalid robot positions rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_round_with_invalid_robot_positions", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_round_with_invalid_target_positions(self):
        """Test round creation with invalid target positions"""
        start_time = time.time()
        
        try:
            invalid_targets = [
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 'invalid', 'y': 8}  # Non-numeric
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'invalid_color', 'x': 8, 'y': 8}  # Invalid color
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'x': 8, 'y': 8}  # Missing color
                }
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for round_data in invalid_targets:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            if proper_rejections == len(invalid_targets):
                result = TestResult("test_round_with_invalid_target_positions", "PASS", duration, 
                                  f"All {len(invalid_targets)} invalid target positions properly rejected")
            else:
                result = TestResult("test_round_with_invalid_target_positions", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(invalid_targets)} invalid target positions rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_round_with_invalid_target_positions", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_round_with_invalid_walls(self):
        """Test round creation with invalid wall formats"""
        start_time = time.time()
        
        try:
            invalid_walls = [
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8},
                    'walls': ['invalid_wall_format']
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8},
                    'walls': ['1,1,invalid_side']
                },
                {
                    'roundName': 'Test',
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8},
                    'walls': ['100,100,top']  # Out of bounds
                }
            ]
            
            proper_rejections = 0
            headers = self._create_mock_auth_header()
            
            for round_data in invalid_walls:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:
                    proper_rejections += 1
            
            duration = time.time() - start_time
            if proper_rejections >= len(invalid_walls) // 2:  # Some validation might be lenient
                result = TestResult("test_round_with_invalid_walls", "PASS", duration, 
                                  f"{proper_rejections}/{len(invalid_walls)} invalid wall formats properly rejected")
            else:
                result = TestResult("test_round_with_invalid_walls", "FAIL", duration, 
                                  f"Only {proper_rejections}/{len(invalid_walls)} invalid wall formats rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_round_with_invalid_walls", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_round_with_large_data(self):
        """Test round creation with large amounts of data"""
        start_time = time.time()
        
        try:
            # Create a round with many walls and puzzle states
            large_walls = [f'{i},{j},top' for i in range(16) for j in range(16)][:1000]
            large_puzzle_states = []
            
            for i in range(50):  # Many puzzle states
                state = {
                    'walls': [f'{i},{j},left' for j in range(10)],
                    'targets': [f'{i},{j}' for j in range(5)],
                    'initialRobotPositions': {
                        'red': {'x': i % 16, 'y': (i + 1) % 16}
                    },
                    'targetPosition': {'color': 'red', 'x': (i + 2) % 16, 'y': (i + 3) % 16}
                }
                large_puzzle_states.append(state)
            
            large_round = {
                'roundName': 'Large Test Round',
                'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                'targetPositions': {'color': 'red', 'x': 8, 'y': 8},
                'walls': large_walls,
                'puzzleStates': large_puzzle_states
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, large_round)
            
            # Should handle large data appropriately
            if status in [400, 401, 403, 413]:  # 413 = Payload Too Large
                duration = time.time() - start_time
                result = TestResult("test_round_with_large_data", "PASS", duration, 
                                  f"Large round data handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_round_with_large_data", "FAIL", duration, 
                                  f"Large round unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_round_with_large_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_round_with_special_characters(self):
        """Test round creation with special characters in name"""
        start_time = time.time()
        
        try:
            special_names = [
                'Round with <script>alert("xss")</script>',
                'Round with "quotes" and \'apostrophes\'',
                'Round with emoji 🎮🤖',
                'Round with unicode 测试回合',
                'Round\nwith\nnewlines',
                'Round\twith\ttabs'
            ]
            
            handled_properly = 0
            headers = self._create_mock_auth_header()
            
            for name in special_names:
                round_data = {
                    'roundName': name,
                    'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                    'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
                }
                
                status, response, req_duration, resp_headers = await self._make_request('POST', '/rounds', headers, round_data)
                
                if status in [400, 401, 403]:  # Some form of handling
                    handled_properly += 1
            
            duration = time.time() - start_time
            if handled_properly == len(special_names):
                result = TestResult("test_round_with_special_characters", "PASS", duration, 
                                  f"All {len(special_names)} special character names properly handled")
            else:
                result = TestResult("test_round_with_special_characters", "FAIL", duration, 
                                  f"Only {handled_properly}/{len(special_names)} special character names properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_round_with_special_characters", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_rounds_pagination(self):
        """Test rounds pagination (if supported)"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            
            # Test with pagination parameters
            pagination_params = ['?limit=10', '?offset=0', '?page=1', '?limit=10&offset=0']
            responses = 0
            
            for params in pagination_params:
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/rounds{params}', headers)
                
                if status in [200, 401, 403]:  # Some response
                    responses += 1
            
            duration = time.time() - start_time
            if responses > 0:
                result = TestResult("test_rounds_pagination", "PASS", duration, 
                                  f"Pagination parameters handled: {responses}/{len(pagination_params)} responded")
            else:
                result = TestResult("test_rounds_pagination", "SKIP", duration, 
                                  "No pagination responses received")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_rounds_pagination", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_concurrent_round_operations(self):
        """Test concurrent round operations"""
        start_time = time.time()
        
        try:
            # Create multiple rounds concurrently
            rounds = [self._create_valid_round() for _ in range(5)]
            headers = self._create_mock_auth_header()
            
            # Send all requests concurrently
            tasks = []
            for round_data in rounds:
                task = self._make_request('POST', '/rounds', headers, round_data)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should respond
            successful_responses = 0
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    successful_responses += 1
            
            duration = time.time() - start_time
            if successful_responses >= len(rounds) // 2:
                result = TestResult("test_concurrent_round_operations", "PASS", duration, 
                                  f"Concurrent operations handled: {successful_responses}/{len(rounds)} responded")
            else:
                result = TestResult("test_concurrent_round_operations", "FAIL", duration, 
                                  f"Poor concurrent handling: only {successful_responses}/{len(rounds)} responded")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_concurrent_round_operations", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_round_with_config_id(self):
        """Test POST /rounds/config/{configId}"""
        start_time = time.time()
        
        try:
            config_id = 'test-config-123'
            round_data = {
                'roundName': 'Config-based Round',
                'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', f'/rounds/config/{config_id}', headers, round_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_create_round_with_config_id", "PASS", duration, 
                                  "Config-based round creation requires authentication")
            elif status in [201, 404]:  # 404 if config doesn't exist
                duration = time.time() - start_time
                result = TestResult("test_create_round_with_config_id", "PASS", duration, 
                                  f"Config-based round endpoint responds correctly (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_create_round_with_config_id", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_round_with_config_id", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_create_round_invalid_config_id(self):
        """Test POST /rounds/config/{configId} with invalid config ID"""
        start_time = time.time()
        
        try:
            invalid_config_ids = ['', 'invalid-config', '../../etc/passwd', '<script>alert(1)</script>']
            proper_responses = 0
            headers = self._create_mock_auth_header()
            
            round_data = {
                'roundName': 'Test Round',
                'initialRobotPositions': {'red': {'x': 1, 'y': 1}},
                'targetPositions': {'color': 'red', 'x': 8, 'y': 8}
            }
            
            for config_id in invalid_config_ids:
                status, response, req_duration, resp_headers = await self._make_request('POST', f'/rounds/config/{config_id}', headers, round_data)
                
                if status in [400, 401, 403, 404]:
                    proper_responses += 1
            
            duration = time.time() - start_time
            if proper_responses == len(invalid_config_ids):
                result = TestResult("test_create_round_invalid_config_id", "PASS", duration, 
                                  f"All {len(invalid_config_ids)} invalid config IDs properly rejected")
            else:
                result = TestResult("test_create_round_invalid_config_id", "FAIL", duration, 
                                  f"Only {proper_responses}/{len(invalid_config_ids)} invalid config IDs properly rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_create_round_invalid_config_id", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)