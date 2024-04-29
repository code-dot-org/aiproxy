import json
import unittest
import numpy as np

from lib.assessment.confidence import get_pass_fail_confidence, get_exact_match_confidence, get_predicted_class_stats

class TestConfidence(unittest.TestCase):
    def test_pass_fail_confidence(self):
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

    def test_predicted_class_stats(self):
        confusion = np.array(
            [[4, 1, 0, 0],
             [5, 1, 0, 0],
             [0, 0, 8, 0],
             [0, 0, 0, 0]]
        )

        expected_counts = [9, 2, 8, 0]
        expected_accuracies = [4/9, 1/2, 8/8, 0]

        counts, accuracies = get_predicted_class_stats(confusion)

        assert counts == expected_counts

        for i in range(len(accuracies)):
            self.assertAlmostEqual(accuracies[i], expected_accuracies[i], 1e-4)

    def test_exact_match_confidence(self):
        confusion1 = np.array(
            [[17, 1, 1, 0],
             [1, 9, 1, 1],
             [1, 0, 15, 1],
             [0, 0, 0, 14]]
        )
        confusion2 = np.array(
            [[5, 1, 0, 0],
             [5, 1, 0, 0],
             [0, 0, 8, 0],
             [0, 0, 0, 0]]
        )

        confusion_by_criteria = {
            "goal1": confusion1,
            "goal2": confusion2
        }

        expected = {
            "goal1": {
                "Extensive Evidence": "HIGH",   # 17 / 19 = 0.8947
                "Convincing Evidence": "HIGH",  #  9 / 10 = 0.9
                "Limited Evidence": "HIGH",     # 15 / 17 = 0.8823
                "No Evidence": "LOW"            # 14 / 16 = 0.875
            },
            "goal2": {
                "Extensive Evidence": "LOW",
                "Convincing Evidence": "LOW",
                "Limited Evidence": "LOW",
                "No Evidence": "LOW"
            }
        }

        assert get_exact_match_confidence(confusion_by_criteria) == expected
