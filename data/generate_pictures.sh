#!/bin.sh

# generate pics and delete empty frames manually

ffmpeg -i 2k_big_1.mp4 -r 2 2k_big_fish__%04d.png
ffmpeg -i 2k_small_1.mp4 -r 2 2k_small_fish__%04d.png
ffmpeg -i 640_big_1.mp4 -r 2 640_big_fish__%04d.png
ffmpeg -i 640_small_1.mp4 -r 2 640_small_fish__%04d.png
