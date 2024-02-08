VALID_LABELS = ["Extensive Evidence", "Convincing Evidence", "Limited Evidence", "No Evidence"]
# do not include gpt-4, so that we always know what version of the model we are using.
SUPPORTED_MODELS = ['gpt-4-0314', 'gpt-4-32k-0314', 'gpt-4-0613', 'gpt-4-32k-0613', 'gpt-4-1106-preview']
DEFAULT_MODEL = 'gpt-4-0613'
LESSONS = ['csd3-2023-L11','csd3-2023-L14','csd3-2023-L18','csd3-2023-L21','csd3-2023-L24','csd3-2023-L28']
DEFAULT_DATASET_NAME = 'contractor-grades-batch-1-fall-2023'
DEFAULT_EXPERIMENT_NAME = 'ai-rubrics-pilot-baseline'
