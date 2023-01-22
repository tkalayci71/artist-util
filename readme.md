# Artist-Util extension version 1.0 - 2023.01.23

for ![AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Extensions)

This extension helps you:
* Browse and categorize artist names, while displaying images from different folders
* Generate prompts for use with 'prompts from file or textbox' script
* Export an HTML file containing all the names and images

![image](screenshots/ss01.jpg)
![image](screenshots/ss02.jpg)

# Installation

Download ![artist-util-main.zip](https://github.com/tkalayci71/artist-util/archive/refs/heads/main.zip) and extract into extensions folder.

[also to see example images you need to extract .zip files in images folder]

# Customization

you can:
* edit artist names in /data/names.txt
* edit wildcard templates in /data/templates.txt
* add category tags by creating empty .txt files in /data/tags/
* add new folders containing bulk generated images, under /images/ (only 1 file per artist name)
* add images in /data/assorted/ folder (set SHOW_ASSORTED = True in script)
* edit some other options in the script, such as HTML export options


