#!/usr/bin/env python3
"""
Base classes for test suites and results
"""

from datetime import datetime
from typing import List, Optional


class TestResult:
    """Represents the result of a single test"""
    def __init__(self, name: str, status: str, duration: float, message: str = "", details: str = ""):
        self.name = name
        self.status = status  # PASS, FAIL, ERROR, SKIP
        self.duration = duration
        self.message = message
        self.details = details
        self.timestamp = datetime.now()


class TestSuite:
    """Represents a collection of test results"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tests: List[TestResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.setup_error: Optional[str] = None
        
    @property
    def total(self) -> int:
        """Total number of tests"""
        return len(self.tests)
        
    @property
    def passed(self) -> int:
        """Number of passed tests"""
        return sum(1 for test in self.tests if test.status == 'PASS')
        
    @property
    def failed(self) -> int:
        """Number of failed tests"""
        return sum(1 for test in self.tests if test.status == 'FAIL')
        
    @property
    def errors(self) -> int:
        """Number of error tests"""
        return sum(1 for test in self.tests if test.status == 'ERROR')
        
    @property
    def skipped(self) -> int:
        """Number of skipped tests"""
        return sum(1 for test in self.tests if test.status == 'SKIP')
        
    @property
    def duration(self) -> float:
        """Total duration of the test suite"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return sum(test.duration for test in self.tests)