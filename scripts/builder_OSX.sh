#####################################
# DSPDemo OSX standalone application
# builder script.
#
# Olivier Belanger, 2018
#####################################

export DMG_DIR="DSPDemo 0.0.9"
export DMG_NAME="DSPDemo_0.0.9.dmg"

python3.6 setup.py py2app --plist=scripts/info.plist

rm -rf build
mv dist DSPDemo_OSX

if cd DSPDemo_OSX;
then
    find . -name .git -depth -exec rm -rf {} \
    find . -name *.pyc -depth -exec rm -f {} \
    find . -name .* -depth -exec rm -f {} \;
else
    echo "Something wrong. DSPDemo_OSX not created"
    exit;
fi

rm DSPDemo.app/Contents/Resources/DSPDemo_Icon.ico

# keep only 64-bit arch
ditto --rsrc --arch x86_64 DSPDemo.app DSPDemo-x86_64.app
rm -rf DSPDemo.app
mv DSPDemo-x86_64.app DSPDemo.app

# Fixed wrong path in Info.plist
cd DSPDemo.app/Contents
awk '{gsub("@executable_path/../Frameworks/Python.framework/Versions/2.7/Python", "@executable_path/../Frameworks/Python.framework/Versions/3.6/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk '{gsub("Library/Frameworks/Python.framework/Versions/3.6/bin/python3.6", "@executable_path/../Frameworks/Python.framework/Versions/3.6/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist

cd ../../..
cp -R DSPDemo_OSX/DSPDemo.app .

echo "assembling DMG..."
mkdir "$DMG_DIR"
cd "$DMG_DIR"
cp -R ../DSPDemo.app .
ln -s /Applications .
cd ..

hdiutil create "$DMG_NAME" -srcfolder "$DMG_DIR"

rm -rf "$DMG_DIR"
rm -rf DSPDemo_OSX
rm -rf DSPDemo.app
