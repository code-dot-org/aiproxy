#!/usr/bin/env python

# Make sure the caller sees a helpful error message if they try to run this script with Python 2
f"This script requires {'Python 3'}. Please be sure to activate your virtual environment via `source .venv/bin/activate`."

import argparse
import csv
import glob
import json
import time
import os
from multiprocessing import Pool
import concurrent.futures
import io
import logging
import pprint
import boto3
import subprocess

from sklearn.metrics import accuracy_score, confusion_matrix
from collections import defaultdict

from lib.assessment.config import SUPPORTED_MODELS, DEFAULT_MODEL, VALID_LABELS, LESSONS, DEFAULT_EXPERIMENT_NAME
from lib.assessment.label import Label
from lib.assessment.report import Report

#globals
prompt_file = 'system_prompt.txt'
standard_rubric_file = 'standard_rubric.csv'
actual_labels_file_old = 'expected_grades.csv'
actual_labels_file = 'actual_labels.csv'
output_dir_name = 'output'
experiments_dir = 'experiments'
cache_dir_name = 'cached_responses'
accuracy_threshold_file = 'accuracy_thresholds.json'
accuracy_threshold_dir = 'tests/data'
s3_bucket = 'cdo-ai'
s3_prefix = 'teaching_assistant/experiments'
params_file = 'params.json'

pp = pprint.PrettyPrinter(indent=2)

def command_line_options():
    parser = argparse.ArgumentParser(description='Usage')

    parser.add_argument('--lesson-names', type=str,
                        help=f"Comma-separated list of lesson names to run. Supported lessons {', '.join(LESSONS)}. Defaults to all lessons.")
    parser.add_argument('-e', '--experiment-name', type=str, default=DEFAULT_EXPERIMENT_NAME,
                        help=f"Name of experiment directory in S3 to load from. Default: {DEFAULT_EXPERIMENT_NAME}.")
    parser.add_argument('-o', '--output-filename', type=str, default='report.html',
                        help='Output filename within output directory')
    parser.add_argument('-c', '--use-cached', action='store_true',
                        help='Use cached responses from the API.')
    parser.add_argument('-l', '--llm-model', type=str, default=DEFAULT_MODEL,
                        help=f"Which LLM model to use. Supported models: {', '.join(SUPPORTED_MODELS)}. Default: {DEFAULT_MODEL}")
    parser.add_argument('-n', '--num-responses', type=int, default=1,
                        help='Number of responses to generate for each student. Defaults to 1.')
    parser.add_argument('-p', '--num-passing-labels', type=int,
                        help='Number of labels which are considered passing.')
    parser.add_argument('-s', '--max-num-students', type=int, default=100,
                        help='Maximum number of students to label. Defaults to 100 students.')
    parser.add_argument('--student-ids', type=str,
                        help='Comma-separated list of student ids to label. Defaults to all students.')
    parser.add_argument('-t', '--temperature', type=float, default=0.0,
                        help='Temperature of the LLM. Defaults to 0.0.')
    parser.add_argument('-d', '--download', action='store_true',
                        help='re-download lesson files, overwriting previous files')
    parser.add_argument('-a', '--accuracy', action='store_true',
                        help='Run against accuracy thresholds')
    parser.add_argument('--params', action='store_true', help="Use params from lesson data files")

    args = parser.parse_args()

    if args.llm_model not in SUPPORTED_MODELS:
        raise Exception(f"Unsupported LLM model: {args.llm_model}. Supported models are: {', '.join(SUPPORTED_MODELS)}")

    args.passing_labels = get_passing_labels(args.num_passing_labels)

    if args.student_ids:
        args.student_ids = args.student_ids.split(',')

    if args.lesson_names:
        args.lesson_names = args.lesson_names.split(',')
    else:
        args.lesson_names = LESSONS

    unsupported_lessons = list(filter(lambda x: x not in LESSONS, args.lesson_names))
    if len(unsupported_lessons) > 0:
        raise Exception(f"Unsupported Lesson names: {', '.join(unsupported_lessons)}. Supported lessons are: {', '.join(LESSONS)}")

    return args


def get_passing_labels(num_passing_labels):
    if num_passing_labels:
        return VALID_LABELS[:num_passing_labels]
    else:
        return None


def read_inputs(prompt_file, standard_rubric_file, prefix):
    with open(os.path.join(prefix, prompt_file), 'r') as f:
        prompt = f.read()

    with open(os.path.join(prefix, standard_rubric_file), 'r') as f:
        standard_rubric = f.read()

    return prompt, standard_rubric

def get_params(prefix):
    params = {}
    with open(os.path.join(prefix, params_file), 'r') as f:
        params = json.load(f)
        for k in params.keys():
            if k == 'model':
                continue
            elif k == 'temperature':
                params[k] = float(params[k])
            else:
                params[k] = int(params[k])
            
    return params

def get_student_files(max_num_students, prefix, student_ids=None):
    if student_ids:
        return [os.path.join(prefix, f"{student_id}.js") for student_id in student_ids]
    else:
        return sorted(glob.glob(os.path.join(prefix, '*.js')))[:max_num_students]


def get_actual_labels(actual_labels_file, prefix):
    actual_labels = {}
    with open(os.path.join(prefix, actual_labels_file), newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            student_id = row['student']
            actual_labels[student_id] = dict(row)
    return actual_labels

def get_accuracy_thresholds(accuracy_threshold_file=accuracy_threshold_file, prefix=accuracy_threshold_dir):
    thresholds = None
    if os.path.exists(os.path.join(prefix, accuracy_threshold_file)):
        with open(os.path.join(prefix, accuracy_threshold_file), 'r') as f:
            thresholds = json.load(f)
    return thresholds


def get_examples(prefix):
    example_js_files = sorted(glob.glob(os.path.join(prefix, 'examples', '*.js')))
    examples = []
    for example_js_file in example_js_files:
        example_id = os.path.splitext(os.path.basename(example_js_file))[0]
        with open(example_js_file, 'r') as f:
            example_code = f.read()
        with open(os.path.join(prefix, 'examples', f"{example_id}.tsv"), 'r') as f:
            example_rubric = f.read()
        examples.append((example_code, example_rubric))
    return examples

def get_s3_folder(s3, experiment_name, lesson_name, prefix):
    print("get_s3_folder args:", experiment_name, lesson_name, prefix)
    bucket = s3.Bucket(s3_bucket)
    for obj in bucket.objects.filter(Prefix="/".join([s3_prefix, experiment_name, lesson_name])):
        target = os.path.join(prefix, os.path.relpath(obj.key, "/".join([s3_prefix, experiment_name, lesson_name])))
        print(f"Copy {obj.key} to {target}")
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        if obj.key[-1] == '/': #recursively download
            continue
        bucket.download_file(obj.key, target)

def validate_rubrics(actual_labels, standard_rubric):
    actual_concepts = sorted(list(list(actual_labels.values())[0].keys())[1:])
    standard_rubric_filelike = io.StringIO(standard_rubric)  # convert string to file-like object
    standard_rubric_dicts = list(csv.DictReader(standard_rubric_filelike))
    standard_concepts = sorted([rubric_dict["Key Concept"] for rubric_dict in standard_rubric_dicts])
    if standard_concepts != actual_concepts:
        raise Exception(f"standard concepts do not match actual concepts:\n{standard_concepts}\n{actual_concepts}")


def validate_students(student_files, actual_labels):
    actual_students = sorted(actual_labels.keys())
    predicted_students = sorted([os.path.splitext(os.path.basename(student_file))[0] for student_file in student_files])

    unexpected_students = list(set(predicted_students) - set(actual_students))
    if unexpected_students:
        raise Exception(f"unexpected students: {unexpected_students}")


def compute_accuracy(actual_labels, predicted_labels, passing_labels):
    actual_by_criteria = defaultdict(list)
    predicted_by_criteria = defaultdict(list)
    confusion_by_criteria = {}
    overall_predicted = []
    overall_actual = []
    label_names = VALID_LABELS

    for student_id, label in predicted_labels.items():
        for row in label:
            criteria = row['Key Concept']
            actual_by_criteria[criteria].append(actual_labels[student_id][criteria])
            predicted_by_criteria[criteria].append(row['Label'])

    accuracy_by_criteria = {}

    for criteria in predicted_by_criteria.keys():
        if (passing_labels):
            pass_string = "/".join(passing_labels)
            fail_string = "/".join([label for label in VALID_LABELS if label not in passing_labels])
            label_names = [pass_string, fail_string]
            predicted_by_criteria[criteria] = list(map(lambda x: pass_string if x in passing_labels else fail_string, predicted_by_criteria[criteria]))
            actual_by_criteria[criteria] = list(map(lambda x: pass_string if x in passing_labels else fail_string, actual_by_criteria[criteria]))
        
        predicted = predicted_by_criteria[criteria]
        actual = actual_by_criteria[criteria]
        
        confusion_by_criteria[criteria] = confusion_matrix(actual, predicted, labels=label_names)
        accuracy_by_criteria[criteria] = accuracy_score(actual, predicted)
        overall_predicted.extend(predicted)
        overall_actual.extend(actual)

    overall_accuracy = accuracy_score(overall_actual, overall_predicted)
    overall_confusion = confusion_matrix(overall_actual, overall_predicted, labels=label_names)

    return accuracy_by_criteria, overall_accuracy, confusion_by_criteria, overall_confusion, label_names


def label_student_work(prompt, rubric, student_file, examples, options, params, prefix):
    student_id = os.path.splitext(os.path.basename(student_file))[0]
    with open(student_file, 'r') as f:
        student_code = f.read()
    label = Label()
    labels = label.label_student_work(
        prompt,
        rubric,
        student_code,
        student_id,
        examples=examples,
        use_cached=options.use_cached,
        write_cached=True,
        num_responses=params['num_responses'] if 'num_responses' in params else options.num_responses,
        temperature=params['temperature'] if 'temperature' in params else options.temperature,
        llm_model=params['model'] if 'model' in params else options.llm_model,
        remove_comments=params['remove_comments'] if 'remove_comments' in params else False,
        cache_prefix=prefix
    )
    return student_id, labels


def main():
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=log_level)

    command_line = " ".join(os.sys.argv)
    options = command_line_options()
    main_start_time = time.time()
    accuracy_failures = {}
    accuracy_pass = True
    accuracy_thresholds = None
    params = {}

    if options.accuracy:
        accuracy_thresholds = get_accuracy_thresholds()

    for lesson in options.lesson_names:
        prefix = os.path.join(experiments_dir, options.experiment_name, lesson)
        data_prefix = os.path.join(prefix, "data")

        # download lesson files
        if not os.path.exists(prefix) or options.download:
            try:
                result = subprocess.run('aws sts get-caller-identity', shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"AWS access configured: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"AWS access not configured: {e} {e.stderr}Please see README.md and make sure you ran `gem install aws-google` and `bin/aws_access`")
                exit(1)
            try:
                s3 = boto3.resource("s3")
                get_s3_folder(s3, options.experiment_name, lesson, prefix)
            except Exception as e:
                print(f"Could not download lesson {lesson}")
                logging.error(e)

        # read in lesson files, validate them
        if options.params:
            params = get_params(prefix)
        prompt, standard_rubric = read_inputs(prompt_file, standard_rubric_file, prefix)
        student_files = get_student_files(options.max_num_students, data_prefix, student_ids=options.student_ids)
        if os.path.exists(os.path.join(data_prefix, actual_labels_file_old)):
            actual_labels = get_actual_labels(actual_labels_file_old, data_prefix)
        else:
            actual_labels = get_actual_labels(actual_labels_file, data_prefix)
        examples = get_examples(prefix)

        validate_rubrics(actual_labels, standard_rubric)
        validate_students(student_files, actual_labels)
        rubric = standard_rubric

        # set up output and cache directories
        output_file = os.path.join(prefix, output_dir_name, options.output_filename)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        os.makedirs(os.path.join(prefix, cache_dir_name), exist_ok=True)
        if not options.use_cached:
            for file in glob.glob(f'{os.path.join(prefix, cache_dir_name)}/*'):
                os.remove(file)

        # call label function to either call openAI or read from cache
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            predicted_labels = list(executor.map(lambda student_file: label_student_work(prompt, rubric, student_file, examples, options, params, prefix), student_files))

        errors = [student_id for student_id, labels in predicted_labels if not labels]
        # predicted_labels contains metadata and data (labels), we care about the data key
        predicted_labels = {student_id: labels['data'] for student_id, labels in predicted_labels if labels}

        # calculate accuracy and generate report
        accuracy_by_criteria, overall_accuracy, confusion_by_criteria, overall_confusion, label_names = compute_accuracy(actual_labels, predicted_labels, options.passing_labels)
        overall_accuracy_percent = overall_accuracy * 100
        accuracy_by_criteria_percent = {k:v*100 for k,v in accuracy_by_criteria.items()}
        report = Report()
        report.generate_html_output(
            output_file,
            prompt,
            rubric,
            accuracy=overall_accuracy_percent,
            predicted_labels=predicted_labels,
            actual_labels=actual_labels,
            passing_labels=options.passing_labels,
            accuracy_by_criteria=accuracy_by_criteria_percent,
            errors=errors,
            command_line=command_line,
            confusion_by_criteria=confusion_by_criteria,
            overall_confusion=overall_confusion,
            label_names=label_names,
            prefix=prefix
        )
        logging.info(f"main finished in {int(time.time() - main_start_time)} seconds")

        if options.accuracy and accuracy_thresholds is not None:
            if overall_accuracy < accuracy_thresholds[lesson]['overall']:
                accuracy_pass = False
                accuracy_failures[lesson] = {}
                accuracy_failures[lesson]['overall'] = {}
                accuracy_failures[lesson]['overall']['accuracy_score'] = overall_accuracy
                accuracy_failures[lesson]['overall']['threshold'] = accuracy_thresholds[lesson]['overall']
            for key_concept in accuracy_by_criteria:
                if accuracy_by_criteria[key_concept] < accuracy_thresholds[lesson]['key_concepts'][key_concept]:
                    accuracy_pass = False
                    if lesson not in accuracy_failures.keys(): accuracy_failures[lesson] = {}
                    if 'key_concepts' not in accuracy_failures[lesson].keys(): accuracy_failures[lesson]['key_concepts'] = {}
                    if key_concept not in accuracy_failures[lesson]['key_concepts'].keys() : accuracy_failures[lesson]['key_concepts'][key_concept] = {}
                    accuracy_failures[lesson]['key_concepts'][key_concept]['accuracy_score'] = accuracy_by_criteria[key_concept]
                    accuracy_failures[lesson]['key_concepts'][key_concept]['threshold'] = accuracy_thresholds[lesson]['key_concepts'][key_concept]

        os.system(f"open {output_file}")

    if not accuracy_pass and len(accuracy_failures.keys()) > 0:
        logging.error(f"The following thresholds were not met:\n{pp.pformat(accuracy_failures)}")
        print(("PASS" if accuracy_pass else "FAIL"))

    return accuracy_pass


def init():
    if __name__ == '__main__':
        main()

init()
