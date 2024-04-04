# Normal imports
import csv, glob, json, time, os
from multiprocessing import Pool
import concurrent.futures
import io
import json
import logging

# Import our support classes
from lib.assessment.config import SUPPORTED_MODELS, DEFAULT_MODEL, VALID_LABELS
from lib.assessment.label import Label

class KeyConceptError(Exception):
  pass

def label(code, prompt, rubric, examples=[], api_key='', llm_model=DEFAULT_MODEL, num_responses=1, temperature=0.2, remove_comments=False, response_type='tsv', code_feature_extractor=None, lesson=None):
  OPENAI_API_KEY = api_key

  # Set the key
  if OPENAI_API_KEY:
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
  elif not 'OPENAI_API_KEY' in os.environ:
    logging.error("Must set OPENAI_API_KEY!")
    return {}
  else:
    logging.info("Using set OPENAI_API_KEY")

  # Validate example key concepts against rubric.
  for i, ex in enumerate(examples):
    rubric_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(rubric.splitlines())))
    example_key_concepts = get_example_key_concepts(ex[1], response_type)
    if rubric_key_concepts != example_key_concepts:
      logging.error(f"Mismatch between rubric and example key concepts for example {i}: Rubric: {rubric_key_concepts} | Example: {example_key_concepts}")
      raise KeyConceptError(f"Mismatch between rubric and example key concepts for example {i}: Rubric: {rubric_key_concepts} | Example: {example_key_concepts}")

  label = Label()
  return label.label_student_work(
      prompt, rubric, code, "student",
      examples=examples,
      use_cached=False,
      write_cached=False,
      num_responses=num_responses,
      temperature=temperature,
      llm_model=llm_model,
      remove_comments=remove_comments,
      response_type=response_type,
      code_feature_extractor=code_feature_extractor,
      lesson=lesson,
  )

def get_example_key_concepts(example_response, response_type):
    if response_type == 'tsv':
        return list(set(row['Key Concept'] for row in csv.DictReader(example_response.splitlines(), delimiter="\t")))
    elif response_type == 'json':
        response_data = json.loads(example_response)
        return list(set([item["Key Concept"] for item in response_data]))
    else:
        raise f"invalid response type {response_type}"
