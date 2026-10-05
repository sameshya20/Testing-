import itertools
from typing import List, Dict, Any

class CombinationEngine:
    """Generates orthogonal parameter combination scenarios from requirements."""

    def derive_combinations(self, user_roles: List[str], input_states: List[str], permissions: List[str]) -> List[Dict[str, str]]:
        """Generates pairwise combinations across user roles, input states, and permission profiles."""
        if not user_roles:
            user_roles = ["Standard User", "Administrator"]
        if not input_states:
            input_states = ["Valid Complete Input", "Missing Mandatory Field", "Boundary Exceeded"]
        if not permissions:
            permissions = ["Authorized", "Unauthorized / Expired Session"]

        combinations = []
        # Generate representative pairwise matrix to maximize coverage while preventing combinatorial explosion
        for role, state, perm in itertools.product(user_roles[:3], input_states[:4], permissions[:2]):
            combinations.append({
                "role": role,
                "input_state": state,
                "permission": perm
            })

        return combinations

combination_engine = CombinationEngine()
