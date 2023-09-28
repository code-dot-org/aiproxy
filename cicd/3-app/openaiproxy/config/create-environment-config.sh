#!/bin/sh

set -e

dir=cicd/3-app/aiproxy

# loop over config files
for i in $(ls "${dir}/config" | egrep -i '.*\.config\.json' ); do
  file="${dir}/config/${i}"
  echo "tranforming ${i}..."
  contents=$(cat $file)

  # New value insertion
  # contents="$(jq '.NewValueDemo = "abcde"' <<< $contents)"

  # Edit existing value
  # if [ "$( jq 'has("TransformDemo")' $file )" == "true" ]; then
  #   ORIGINAL_VALUE=$(jq -r  '.TransformDemo' $file)
  #   NEW_VALUE=$(date '+%s')
  #   echo "replacing '${ORIGINAL_VALUE}' with '${NEW_VALUE}'"
  #   contents="$(jq ".TransformDemo = ${NEW_VALUE}" <<< $contents)"
  #   # jq ".TransformDemo = ${NEW_VALUE}" $file > $file
  # fi

  echo "${contents}" > "${dir}/${i}"
done
