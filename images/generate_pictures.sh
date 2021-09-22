#!/usr/bin/bash

# generate pics and delete empty frames manually

for f in *.mp4
do
	echo "Processing $f..."
	ffmpeg -i $f -r 4 -q:v 2 $f%04d.jpeg
done
