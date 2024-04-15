import json

class TestConfidence:
    def test_pass_fail_confidence(self):
        from lib.assessment.confidence import get_pass_fail_confidence

        learning_goal_accuracies = {
            "goal1": 0.9,
            "goal2": 0.8,
            "goal3": 0.7
        }

        expected = {
            "goal1": "HIGH",
            "goal2": "MEDIUM",
            "goal3": "LOW"
        }

        assert get_pass_fail_confidence(learning_goal_accuracies) == expected
