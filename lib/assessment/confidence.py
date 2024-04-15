import json
import logging
import os

def get_pass_fail_confidence(accuracy: dict) -> str:
    """
    This function takes a dictionary of learning goals and their respective accuracies and returns a dictionary of
    learning goals and their respective confidence levels.
    """
    confidence = {}

    for learning_goal in accuracy:
        if accuracy[learning_goal] >= 0.85:
            confidence[learning_goal] = "HIGH"
        elif accuracy[learning_goal] >= 0.8:
            confidence[learning_goal] = "MEDIUM"
        else:
            confidence[learning_goal] = "LOW"

    return confidence
