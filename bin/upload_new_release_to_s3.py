import boto3
import os
import datetime
import argparse

parser = argparse.ArgumentParser(description='Usage')
parser.add_argument('-r','--release-name', type=str,
                    help="Name of release")
args = parser.parse_args()

if not args.release_name:
  raise Exception("Please include a name for your release")

s3 = boto3.client('s3')
now = datetime.date.today()
release_name = f"{now}-{args.release_name}"

def recursive_upload(dir = None, parent_dirs=None):
  home_path = os.path.join(os.path.expanduser('~'), "aitt_release_data")
  if parent_dirs and dir:
    full_path = os.path.join(home_path, parent_dirs, dir)
    new_parent_dirs = os.path.join(parent_dirs, dir)
  elif dir and not parent_dirs:
    full_path = os.path.join(home_path, dir)
    new_parent_dirs = dir
  else:
    full_path = home_path
    new_parent_dirs = None
  
  files = os.listdir(full_path)
  if '.git' in files:
    files.remove('.git')
  if 'README.md' in files:
    files.remove('README.md')
  for f in files:
    f_path = os.path.join(full_path, f)
    if os.path.isfile(f_path):
      if new_parent_dirs:
        print(f"uploading {f_path} to s3:cdo-ai/teaching_assistant/releases/{release_name}/{new_parent_dirs}/{f}")
        s3.upload_file(f_path, 'cdo-ai', f"teaching_assistant/releases/{release_name}/{new_parent_dirs}/{f}")
      else:
        print(f"uploading {f_path} to s3:cdo-ai/teaching_assistant/releases/{release_name}/{f}")
        s3.upload_file(f_path, 'cdo-ai', f"teaching_assistant/releases/{release_name}/{f}")
    elif os.path.isdir(f_path):
      recursive_upload(f, new_parent_dirs)

recursive_upload()

print(f"Upload complete! Update S3_AI_RELEASE_PATH at cdo/dashboard/app/jobs/concerns/ai_rubric_config.rb with the new release location: 'teaching_assistant/releases/{release_name}/'")
