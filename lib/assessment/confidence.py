import json
import logging
import os
import numpy as np

from lib.assessment.config import VALID_LABELS

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


def get_exact_match_confidence(confusion_by_criteria: dict) -> dict:
    """
    This function takes a dictionary of confusion matrices and returns a nested dictionary of learning goals and
    evidence levels mapped to their respective confidence levels.
    """
    confidence = {}

    for learning_goal in confusion_by_criteria:
        confidence[learning_goal] = {}
        confusion = confusion_by_criteria[learning_goal]
        counts, accuracies = get_predicted_class_stats(confusion)
        for i in range(len(VALID_LABELS)):
            label = VALID_LABELS[i]
            if accuracies[i] >= 0.88 and counts[i] >= 10:
                confidence[learning_goal][label] = "HIGH"
            else:
                confidence[learning_goal][label] = "LOW"

    return confidence

def get_predicted_class_stats(confusion):
    """
    compute count and accuracy for each predicted class (column) in the confusion matrix
    """
    counts = []
    accuracies = []

    for i in range(len(confusion)):
        col_sum = np.sum(confusion[:, i])
        counts.append(col_sum)
        accuracies.append(confusion[i, i] / col_sum if col_sum > 0 else 0)

    return counts, accuracies
