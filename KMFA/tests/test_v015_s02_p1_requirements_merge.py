from __future__ import annotations

import unittest

from KMFA.tools.build_v015_s02_p1_requirements_merge import expected_core_outputs
from KMFA.tools.check_v015_s02_p1_requirements_merge import (
    validate_v015_s02_p1_requirements_merge,
)


class TestV015S02P1RequirementsMerge(unittest.TestCase):
    def test_builder_and_validator_contract_is_available(self) -> None:
        self.assertTrue(callable(expected_core_outputs))
        self.assertTrue(callable(validate_v015_s02_p1_requirements_merge))


if __name__ == "__main__":
    unittest.main()
