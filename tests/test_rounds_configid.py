#!/usr/bin/env python3
"""
Test to verify that all rounds have configId present
"""

import json
import requests
from test_base import TestBase

class TestRoundsConfigId(TestBase):
    def test_all_rounds_have_configid(self):
        """Test that all rounds returned by the API have configId"""
        print("\n=== Testing that all rounds have configId ===")
        
        # Get all rounds from the API
        response = requests.get(
            f"{self.base_url}/rounds/solved",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200, 
                        f"Failed to get rounds: {response.status_code} - {response.text}")
        
        rounds = response.json()
        self.assertIsInstance(rounds, list, "Expected rounds to be a list")
        
        if not rounds:
            print("No rounds found in database - skipping configId validation")
            return
        
        missing_configid_rounds = []
        for round_data in rounds:
            if not round_data.get('configId'):
                missing_configid_rounds.append(round_data.get('roundId', 'unknown'))
        
        if missing_configid_rounds:
            self.fail(f"Found {len(missing_configid_rounds)} rounds missing configId: {missing_configid_rounds}")
        
        print(f"✅ All {len(rounds)} rounds have configId present")

    def test_specific_round_has_configid(self):
        """Test that specific round retrieval includes configId"""
        print("\n=== Testing that specific round has configId ===")
        
        # First get a list of rounds
        response = requests.get(
            f"{self.base_url}/rounds/solved",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200, 
                        f"Failed to get rounds: {response.status_code} - {response.text}")
        
        rounds = response.json()
        if not rounds:
            print("No rounds found in database - skipping specific round configId test")
            return
        
        # Get a specific round
        test_round_id = rounds[0]['roundId']
        response = requests.get(
            f"{self.base_url}/rounds/{test_round_id}",
            headers=self.get_auth_headers()
        )
        
        self.assertEqual(response.status_code, 200, 
                        f"Failed to get specific round: {response.status_code} - {response.text}")
        
        round_data = response.json()
        self.assertIsInstance(round_data, dict, "Expected round data to be a dict")
        
        config_id = round_data.get('configId')
        self.assertIsNotNone(config_id, "Round is missing configId")
        self.assertNotEqual(config_id, '', "Round has empty configId")
        
        print(f"✅ Specific round {test_round_id} has configId: {config_id}")

    def test_round_creation_requires_configid(self):
        """Test that round creation requires configId"""
        print("\n=== Testing that round creation requires configId ===")
        
        # Try to create a round without configId
        round_data = {
            "initialRobotPositions": {
                "red": {"x": 0, "y": 0, "color": "red"},
                "blue": {"x": 1, "y": 1, "color": "blue"}
            },
            "targetPositions": {"x": 8, "y": 8, "color": "red"}
        }
        
        response = requests.post(
            f"{self.base_url}/rounds",
            headers=self.get_auth_headers(),
            json=round_data
        )
        
        # Should fail with 400 Bad Request
        self.assertEqual(response.status_code, 400, 
                        f"Expected 400 error for missing configId, got {response.status_code}")
        
        error_response = response.json()
        self.assertIn('configId', error_response.get('error', '').lower(), 
                     "Error message should mention configId")
        
        print("✅ Round creation correctly requires configId")

if __name__ == '__main__':
    import unittest
    unittest.main()