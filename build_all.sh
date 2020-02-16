#!/bin/bash

# This script is not to be used by anyone except me *per se*. It's more of a way to document how I do it.
# I spin up an Ubuntu 16.04 at DigitalOcean and execute this script.
# Then I SCP the AppImages off the thing and turn it off: `scp root@13.37.69.42:"/root/love-appimages/*.AppImage" .`

# I clone the repo three times for trouble shooting. Sometimes stuff doesn't work and I don't want to rebuild
# every time. I just want to tweak and try again. One day when I have done this a couple dozen times and everything
# went smooth I might change this, but it doesn't cost much either way.

sudo apt update
sudo apt install -y autoconf
sudo apt install -y libtool
sudo apt install -y libsdl2-dev
sudo apt install -y libluajit-5.1-dev
sudo apt install -y libfreetype6-dev
sudo apt install -y libopenal-dev
sudo apt install -y libmodplug-dev
sudo apt install -y libvorbis-dev
sudo apt install -y libvorbisfile3
sudo apt install -y libtheora-dev
sudo apt install -y libphysfs-dev
sudo apt install -y libmpg123-dev
sudo apt install -y libdevil-dev

git clone https://github.com/pfirsich/love-appimages.git

git clone https://github.com/love2d/love.git love_0_9_2
cd love_0_9_2
git checkout 0.9.2
./platform/unix/automagic
./configure
git apply ../love-appimages/fix_0_9_2.patch
make
cd ..

git clone https://github.com/love2d/love.git love_0_10_2
cd love_0_10_2
git checkout 0.10.2
./platform/unix/automagic
./configure
git apply ../love-appimages/fix_0_10_2.patch
make
cd ..

git clone https://github.com/love2d/love.git love_11_3
cd love_11_3
git checkout 11.3
./platform/unix/automagic
./configure
make
cd ..

wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
ln -s $(pwd)/appimagetool-x86_64.AppImage appimagetool
chmod +x appimagetool
sudo apt install -y appstream

export PATH="$PATH:/root"
cd love-appimages
python3 build.py ~/love_0_9_2/ AppDir_0_9_2 --appimage love-0.9.2-x86_64.AppImage
python3 build.py ~/love_0_10_2/ AppDir_0_10_2 --appimage love-0.10.2-x86_64.AppImage
python3 build.py ~/love_11_3/ AppDir_11_3 --appimage love-11.3-x86_64.AppImage
