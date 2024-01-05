# Normal imports
import csv, glob, json, time, os
from multiprocessing import Pool
import concurrent.futures
import io
import json
import logging

# Import our support classes
from lib.assessment.config import SUPPORTED_MODELS, VALID_LABELS
from lib.assessment.grade import Grade

class KeyConceptError(Exception):
  pass

def grade(code, prompt, rubric, examples=[], api_key='', llm_model='gpt-4', num_responses=1, temperature=0.2, remove_comments=False):
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
    example_key_concepts = list(set(row['Key Concept'] for row in csv.DictReader(ex[1].splitlines(), delimiter="\t")))
    if rubric_key_concepts != example_key_concepts:
      logging.error(f"Mismatch between rubric and example key concepts for example {i}: Rubric: {rubric_key_concepts} | Example: {example_key_concepts}")
      raise KeyConceptError(f"Mismatch between rubric and example key concepts for example {i}: Rubric: {rubric_key_concepts} | Example: {example_key_concepts}")

  grade = Grade()
  return grade.grade_student_work(
      prompt, rubric, code, "student",
      examples=examples,
      use_cached=False,
      write_cached=False,
      num_responses=num_responses,
      temperature=temperature,
      llm_model=llm_model,
      remove_comments=remove_comments
  )
