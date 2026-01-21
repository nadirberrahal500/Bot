#!/usr/bin/env bash
exit on error
set -o errexit

pip install -r requirements.txt

# تحميل ffmpeg بشكل تلقائي
mkdir -p ffmpeg
cd ffmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*-amd64-static/ffmpeg ..
mv ffmpeg-*-amd64-static/ffprobe ..
cd ..
rm -rf ffmpeg