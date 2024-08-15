VALID_LABELS = ["Extensive Evidence", "Convincing Evidence", "Limited Evidence", "No Evidence"]

PASSING_LABELS = VALID_LABELS[:2]

# do not include gpt-4, so that we always know what version of the model we are using.
SUPPORTED_MODELS = [
    'bedrock.anthropic.claude-v2',
    'bedrock.anthropic.claude-3-sonnet-20240229-v1:0',
    'bedrock.anthropic.claude-3-5-sonnet-20240620-v1:0',
    'bedrock.meta.llama2-13b-chat-v1',
    'bedrock.meta.llama2-70b-chat-v1',
    'gpt-3.5-turbo-0125',
    'gpt-4-0314',
    'gpt-4-32k-0314',
    'gpt-4-0613',
    'gpt-4-32k-0613',
    'gpt-4-1106-preview',
    'gpt-4-0125-preview',
    'gpt-4-turbo-2024-04-09'
]
DEFAULT_MODEL = 'bedrock.anthropic.claude-3-5-sonnet-20240620-v1:0'
LESSONS = ['csd3-2023-L11','csd3-2023-L14','csd3-2023-L18','csd3-2023-L21','csd3-2023-L24','csd3-2023-L28']
DEFAULT_DATASET_NAME = 'contractor-grades-batch-1-fall-2023'

OPENAI_API_TIMEOUT = 150
