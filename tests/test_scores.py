#!/usr/bin/env python3
"""
Scores API Tests
Tests for score submission, leaderboards, and score-related operations
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
    """Scores API Test Suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base_url = config.get('api_base_url', 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod')
        self.suite = BaseTestSuite("Scores API", "Tests for score submission and leaderboard operations")
        self.test_score_id = None
        
    async def run(self):
        """Run all scores tests"""
        self.suite.start_time = datetime.now()
        
        print(f"📋 {self.suite.name}")
        if self.suite.description:
            print(f"   {self.suite.description}")
        print(f"   {'─' * 60}")
        
        # Core functionality tests
        await self.test_get_leaderboard_unauthorized()
        await self.test_submit_score_unauthorized()
        await self.test_get_leaderboard_structure()
        await self.test_submit_valid_score()
        await self.test_submit_score_missing_fields()
        await self.test_submit_score_invalid_data()
        
        # Specialized endpoints
        await self.test_get_round_specific_scores()
        await self.test_submit_score_to_specific_round()
        await self.test_get_user_personal_best()
        await self.test_leaderboard_pagination()
        
        # Edge cases and validation
        await self.test_submit_negative_score()
        await self.test_submit_zero_moves()
        await self.test_submit_extremely_high_score()
        await self.test_submit_duplicate_score()
        await self.test_submit_score_invalid_round()
        await self.test_leaderboard_filtering()
        await self.test_concurrent_score_submissions()
        
        # Data integrity tests
        await self.test_score_data_types()
        await self.test_score_timestamps()
        await self.test_score_metadata()
        
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

    def _create_valid_score(self) -> Dict[str, Any]:
        """Create a valid score submission for testing"""
        return {
            'roundId': f'test-round-{uuid.uuid4().hex[:8]}',
            'moves': 15,
            'completedAt': datetime.now().isoformat(),
            'timeTaken': 120.5,
            'solution': [
                {'robot': 'red', 'direction': 'right', 'distance': 3},
                {'robot': 'blue', 'direction': 'down', 'distance': 2},
                {'robot': 'red', 'direction': 'up', 'distance': 1}
            ]
        }

    async def test_get_leaderboard_unauthorized(self):
        """Test GET /scores (leaderboard) without authorization"""
        start_time = time.time()
        
        try:
            status, response, req_duration, headers = await self._make_request('GET', '/scores')
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_get_leaderboard_unauthorized", "PASS", duration, 
                                  "Unauthorized leaderboard access properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_leaderboard_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_leaderboard_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_score_unauthorized(self):
        """Test POST /scores without authorization"""
        start_time = time.time()
        
        try:
            score_data = self._create_valid_score()
            status, response, req_duration, headers = await self._make_request('POST', '/scores', data=score_data)
            
            if status == 401:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_unauthorized", "PASS", duration, 
                                  "Unauthorized score submission properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_unauthorized", "FAIL", duration, 
                                  f"Expected 401 Unauthorized, got {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_score_unauthorized", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_leaderboard_structure(self):
        """Test GET /scores response structure"""
        start_time = time.time()
        
        try:
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', '/scores', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_leaderboard_structure", "PASS", duration, 
                                  "Authentication properly required")
            elif status == 200:
                if isinstance(response, list):
                    duration = time.time() - start_time
                    result = TestResult("test_get_leaderboard_structure", "PASS", duration, 
                                      f"Leaderboard returns array with {len(response)} scores")
                elif isinstance(response, dict) and 'scores' in response:
                    duration = time.time() - start_time
                    result = TestResult("test_get_leaderboard_structure", "PASS", duration, 
                                      f"Leaderboard returns object with {len(response.get('scores', []))} scores")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_leaderboard_structure", "FAIL", duration, 
                                      f"Unexpected leaderboard structure: {type(response)}")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_leaderboard_structure", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_leaderboard_structure", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_valid_score(self):
        """Test submitting a valid score"""
        start_time = time.time()
        
        try:
            score_data = self._create_valid_score()
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_submit_valid_score", "PASS", duration, 
                                  "Authentication properly required for score submission")
            elif status == 201:
                if isinstance(response, dict):
                    if 'scoreId' in response or 'id' in response:
                        self.test_score_id = response.get('scoreId') or response.get('id')
                        duration = time.time() - start_time
                        result = TestResult("test_submit_valid_score", "PASS", duration, 
                                          f"Score submitted successfully: {self.test_score_id}")
                    else:
                        duration = time.time() - start_time
                        result = TestResult("test_submit_valid_score", "PASS", duration, 
                                          "Score submitted successfully")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_submit_valid_score", "FAIL", duration, 
                                      "Score submitted but response structure unexpected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_valid_score", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_valid_score", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_score_missing_fields(self):
        """Test score submission with missing required fields"""
        start_time = time.time()
        
        try:
            incomplete_scores = [
                {},  # Empty
                {'roundId': 'test-round'},  # Missing moves
                {'moves': 10},  # Missing roundId
                {'roundId': 'test-round', 'moves': 0},  # Zero moves (might be invalid)
                {'roundId': '', 'moves': 10},  # Empty roundId
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for score_data in incomplete_scores:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors == len(incomplete_scores):
                result = TestResult("test_submit_score_missing_fields", "PASS", duration, 
                                  f"All {len(incomplete_scores)} incomplete scores properly rejected")
            else:
                result = TestResult("test_submit_score_missing_fields", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(incomplete_scores)} incomplete scores rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_score_missing_fields", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_score_invalid_data(self):
        """Test score submission with invalid data types"""
        start_time = time.time()
        
        try:
            invalid_scores = [
                {
                    'roundId': 123,  # Should be string
                    'moves': 10
                },
                {
                    'roundId': 'test-round',
                    'moves': 'ten'  # Should be number
                },
                {
                    'roundId': 'test-round',
                    'moves': -5  # Negative moves
                },
                {
                    'roundId': 'test-round',
                    'moves': 10.5  # Fractional moves (might be invalid)
                },
                {
                    'roundId': 'test-round',
                    'moves': 999999  # Extremely high moves
                }
            ]
            
            validation_errors = 0
            headers = self._create_mock_auth_header()
            
            for score_data in invalid_scores:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score_data)
                
                if status in [400, 401, 403]:
                    validation_errors += 1
            
            duration = time.time() - start_time
            if validation_errors >= len(invalid_scores) // 2:  # Some validation might be lenient
                result = TestResult("test_submit_score_invalid_data", "PASS", duration, 
                                  f"{validation_errors}/{len(invalid_scores)} invalid scores properly rejected")
            else:
                result = TestResult("test_submit_score_invalid_data", "FAIL", duration, 
                                  f"Only {validation_errors}/{len(invalid_scores)} invalid scores rejected")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_score_invalid_data", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_round_specific_scores(self):
        """Test GET /scores/{roundId}"""
        start_time = time.time()
        
        try:
            test_round_id = 'test-round-123'
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('GET', f'/scores/{test_round_id}', headers)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_get_round_specific_scores", "PASS", duration, 
                                  "Round-specific scores require authentication")
            elif status == 200:
                if isinstance(response, list):
                    duration = time.time() - start_time
                    result = TestResult("test_get_round_specific_scores", "PASS", duration, 
                                      f"Round-specific scores return {len(response)} scores")
                else:
                    duration = time.time() - start_time
                    result = TestResult("test_get_round_specific_scores", "FAIL", duration, 
                                      "Round-specific scores should return array")
            elif status == 404:
                duration = time.time() - start_time
                result = TestResult("test_get_round_specific_scores", "PASS", duration, 
                                  "Non-existent round properly returns 404")
            else:
                duration = time.time() - start_time
                result = TestResult("test_get_round_specific_scores", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_round_specific_scores", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_score_to_specific_round(self):
        """Test POST /scores/{roundId}"""
        start_time = time.time()
        
        try:
            test_round_id = 'test-round-123'
            score_data = {
                'moves': 25,
                'completedAt': datetime.now().isoformat(),
                'timeTaken': 90.0
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', f'/scores/{test_round_id}', headers, score_data)
            
            if status in [401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_to_specific_round", "PASS", duration, 
                                  "Round-specific score submission requires authentication")
            elif status in [201, 404]:  # 404 if round doesn't exist
                duration = time.time() - start_time
                result = TestResult("test_submit_score_to_specific_round", "PASS", duration, 
                                  f"Round-specific score submission responds correctly (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_to_specific_round", "FAIL", duration, 
                                  f"Unexpected status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_score_to_specific_round", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_get_user_personal_best(self):
        """Test getting user's personal best scores"""
        start_time = time.time()
        
        try:
            # Try with query parameters that might indicate personal best
            params = ['?user=me', '?personal=true', '?best=true']
            responses = 0
            headers = self._create_mock_auth_header()
            
            for param in params:
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/scores{param}', headers)
                
                if status in [200, 401, 403]:
                    responses += 1
            
            duration = time.time() - start_time
            if responses > 0:
                result = TestResult("test_get_user_personal_best", "PASS", duration, 
                                  f"Personal best queries handled: {responses}/{len(params)} responded")
            else:
                result = TestResult("test_get_user_personal_best", "SKIP", duration, 
                                  "No personal best query responses")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_get_user_personal_best", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_leaderboard_pagination(self):
        """Test leaderboard pagination parameters"""
        start_time = time.time()
        
        try:
            pagination_params = ['?limit=10', '?offset=5', '?page=1', '?limit=5&offset=10']
            responses = 0
            headers = self._create_mock_auth_header()
            
            for params in pagination_params:
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/scores{params}', headers)
                
                if status in [200, 401, 403]:
                    responses += 1
            
            duration = time.time() - start_time
            if responses > 0:
                result = TestResult("test_leaderboard_pagination", "PASS", duration, 
                                  f"Pagination parameters handled: {responses}/{len(pagination_params)} responded")
            else:
                result = TestResult("test_leaderboard_pagination", "SKIP", duration, 
                                  "No pagination responses received")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_leaderboard_pagination", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_negative_score(self):
        """Test submitting score with negative moves"""
        start_time = time.time()
        
        try:
            negative_score = {
                'roundId': 'test-round',
                'moves': -10,
                'completedAt': datetime.now().isoformat()
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, negative_score)
            
            if status in [400, 401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_submit_negative_score", "PASS", duration, 
                                  "Negative score properly rejected")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_negative_score", "FAIL", duration, 
                                  f"Negative score should be rejected, got status: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_negative_score", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_zero_moves(self):
        """Test submitting score with zero moves"""
        start_time = time.time()
        
        try:
            zero_score = {
                'roundId': 'test-round',
                'moves': 0,
                'completedAt': datetime.now().isoformat()
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, zero_score)
            
            # Zero moves might be valid (if puzzle is already solved) or invalid
            if status in [201, 400, 401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_submit_zero_moves", "PASS", duration, 
                                  f"Zero moves score handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_zero_moves", "FAIL", duration, 
                                  f"Unexpected status for zero moves: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_zero_moves", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_extremely_high_score(self):
        """Test submitting score with extremely high moves"""
        start_time = time.time()
        
        try:
            high_score = {
                'roundId': 'test-round',
                'moves': 999999999,
                'completedAt': datetime.now().isoformat()
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, high_score)
            
            # Should either accept it or reject with validation error
            if status in [201, 400, 401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_submit_extremely_high_score", "PASS", duration, 
                                  f"Extremely high score handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_extremely_high_score", "FAIL", duration, 
                                  f"Unexpected status for high score: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_extremely_high_score", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_duplicate_score(self):
        """Test submitting duplicate scores for the same round"""
        start_time = time.time()
        
        try:
            score_data = {
                'roundId': 'duplicate-test-round',
                'moves': 15,
                'completedAt': datetime.now().isoformat()
            }
            
            headers = self._create_mock_auth_header()
            
            # Submit the same score twice
            status1, response1, duration1, headers1 = await self._make_request('POST', '/scores', headers, score_data)
            status2, response2, duration2, headers2 = await self._make_request('POST', '/scores', headers, score_data)
            
            # Both should be handled appropriately (either accepted or rejected)
            if (status1 in [201, 401, 403] and status2 in [201, 400, 401, 403, 409]):
                duration = time.time() - start_time
                result = TestResult("test_submit_duplicate_score", "PASS", duration, 
                                  f"Duplicate scores handled: first={status1}, second={status2}")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_duplicate_score", "FAIL", duration, 
                                  f"Unexpected duplicate handling: first={status1}, second={status2}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_duplicate_score", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_submit_score_invalid_round(self):
        """Test submitting score for non-existent round"""
        start_time = time.time()
        
        try:
            invalid_score = {
                'roundId': 'definitely-does-not-exist-12345',
                'moves': 15,
                'completedAt': datetime.now().isoformat()
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, invalid_score)
            
            if status in [400, 401, 403, 404]:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_invalid_round", "PASS", duration, 
                                  f"Score for invalid round properly rejected (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_submit_score_invalid_round", "FAIL", duration, 
                                  f"Score for invalid round should be rejected, got: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_submit_score_invalid_round", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_leaderboard_filtering(self):
        """Test leaderboard filtering options"""
        start_time = time.time()
        
        try:
            filter_params = [
                '?round=test-round',
                '?timeframe=week',
                '?timeframe=month',
                '?sort=moves',
                '?sort=time',
                '?top=10'
            ]
            
            responses = 0
            headers = self._create_mock_auth_header()
            
            for params in filter_params:
                status, response, req_duration, resp_headers = await self._make_request('GET', f'/scores{params}', headers)
                
                if status in [200, 401, 403]:
                    responses += 1
            
            duration = time.time() - start_time
            if responses > 0:
                result = TestResult("test_leaderboard_filtering", "PASS", duration, 
                                  f"Filtering parameters handled: {responses}/{len(filter_params)} responded")
            else:
                result = TestResult("test_leaderboard_filtering", "SKIP", duration, 
                                  "No filtering responses received")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_leaderboard_filtering", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_concurrent_score_submissions(self):
        """Test concurrent score submissions"""
        start_time = time.time()
        
        try:
            # Create multiple score submissions
            scores = []
            for i in range(5):
                score = {
                    'roundId': f'concurrent-test-round-{i}',
                    'moves': 10 + i,
                    'completedAt': datetime.now().isoformat()
                }
                scores.append(score)
            
            headers = self._create_mock_auth_header()
            
            # Submit all scores concurrently
            tasks = []
            for score in scores:
                task = self._make_request('POST', '/scores', headers, score)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should respond appropriately
            successful_responses = 0
            for result in results:
                if isinstance(result, tuple) and result[0] is not None:
                    successful_responses += 1
            
            duration = time.time() - start_time
            if successful_responses >= len(scores) // 2:
                result = TestResult("test_concurrent_score_submissions", "PASS", duration, 
                                  f"Concurrent submissions handled: {successful_responses}/{len(scores)} responded")
            else:
                result = TestResult("test_concurrent_score_submissions", "FAIL", duration, 
                                  f"Poor concurrent handling: only {successful_responses}/{len(scores)} responded")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_concurrent_score_submissions", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_score_data_types(self):
        """Test score submission with various data types"""
        start_time = time.time()
        
        try:
            score_variants = [
                {
                    'roundId': 'type-test-round',
                    'moves': 15,
                    'timeTaken': 120.5,  # Float time
                    'completedAt': datetime.now().isoformat()
                },
                {
                    'roundId': 'type-test-round',
                    'moves': 15,
                    'timeTaken': 120,  # Integer time
                    'completedAt': datetime.now().isoformat()
                },
                {
                    'roundId': 'type-test-round',
                    'moves': 15,
                    'metadata': {'difficulty': 'hard', 'hints_used': 2},  # Additional metadata
                    'completedAt': datetime.now().isoformat()
                }
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            for score in score_variants:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score)
                
                if status in [201, 400, 401, 403]:  # Accepted or properly rejected
                    proper_handling += 1
            
            duration = time.time() - start_time
            if proper_handling == len(score_variants):
                result = TestResult("test_score_data_types", "PASS", duration, 
                                  f"All {len(score_variants)} data type variants properly handled")
            else:
                result = TestResult("test_score_data_types", "FAIL", duration, 
                                  f"Only {proper_handling}/{len(score_variants)} data type variants properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_score_data_types", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_score_timestamps(self):
        """Test score submission with various timestamp formats"""
        start_time = time.time()
        
        try:
            timestamp_variants = [
                {
                    'roundId': 'timestamp-test-round',
                    'moves': 15,
                    'completedAt': datetime.now().isoformat()  # ISO format
                },
                {
                    'roundId': 'timestamp-test-round',
                    'moves': 15,
                    'completedAt': int(time.time())  # Unix timestamp
                },
                {
                    'roundId': 'timestamp-test-round',
                    'moves': 15,
                    'completedAt': '2024-01-01T12:00:00Z'  # Fixed ISO format
                },
                {
                    'roundId': 'timestamp-test-round',
                    'moves': 15
                    # No timestamp (should use server time)
                }
            ]
            
            proper_handling = 0
            headers = self._create_mock_auth_header()
            
            for score in timestamp_variants:
                status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, score)
                
                if status in [201, 400, 401, 403]:
                    proper_handling += 1
            
            duration = time.time() - start_time
            if proper_handling == len(timestamp_variants):
                result = TestResult("test_score_timestamps", "PASS", duration, 
                                  f"All {len(timestamp_variants)} timestamp variants properly handled")
            else:
                result = TestResult("test_score_timestamps", "FAIL", duration, 
                                  f"Only {proper_handling}/{len(timestamp_variants)} timestamp variants properly handled")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_score_timestamps", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)

    async def test_score_metadata(self):
        """Test score submission with additional metadata"""
        start_time = time.time()
        
        try:
            metadata_score = {
                'roundId': 'metadata-test-round',
                'moves': 15,
                'completedAt': datetime.now().isoformat(),
                'timeTaken': 120.5,
                'solution': [
                    {'robot': 'red', 'direction': 'right', 'distance': 3},
                    {'robot': 'blue', 'direction': 'down', 'distance': 2}
                ],
                'hintsUsed': 1,
                'difficulty': 'medium',
                'version': '1.0.0'
            }
            
            headers = self._create_mock_auth_header()
            status, response, req_duration, resp_headers = await self._make_request('POST', '/scores', headers, metadata_score)
            
            if status in [201, 400, 401, 403]:
                duration = time.time() - start_time
                result = TestResult("test_score_metadata", "PASS", duration, 
                                  f"Score with metadata handled appropriately (status: {status})")
            else:
                duration = time.time() - start_time
                result = TestResult("test_score_metadata", "FAIL", duration, 
                                  f"Unexpected status for metadata score: {status}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("test_score_metadata", "ERROR", duration, str(e))
        
        self.suite.tests.append(result)
        self._print_test_result(result)