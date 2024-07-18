import argparse
import os
import subprocess
import datetime

def command_line_options():
    parser = argparse.ArgumentParser(description='Usage')

    parser.add_argument('-e', '--experiment-name', type=str,
                        help=f"Name of experiment branch to push changes.")
    
    parser.add_argument('-m', '--message', type=str,
                        help=f"Commit message.")

    return parser.parse_args()

def push_experiment_updates(branch, message=f"update {datetime.datetime.now()}"):
  subprocess.run(["git", "commit", "-a", "-m", message], cwd=f"./experiments/{branch}")
  subprocess.run(["git", "push"], cwd=f"./experiments/{branch}")

def main():
    options = command_line_options()
    if not options.experiment_name:
        raise Exception("Experiment name required")
    if options.message:
        push_experiment_updates(options.experiment_name, options.message)
    else:
        push_experiment_updates(options.experiment_name)
    

def init():
    if __name__ == '__main__':
        main()

init()
