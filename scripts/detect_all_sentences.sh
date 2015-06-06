#!/bin/bash

# Author: Devon Fritz
# Date: 6.6.2015
# Runs our detect sentences program for every dataset in the folder
echo $1
echo $2
for f in "$1"/*.ltmp
do
	echo "Processing: $f"
	python detect_sentences.py $f $2 >> sentence_results
done
