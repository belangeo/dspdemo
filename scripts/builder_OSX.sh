#####################################
# DSPDemo OSX standalone application
# builder script.
#
# Olivier Belanger, 2020
#####################################

export DMG_DIR="DSPDemo 0.2.0"
export DMG_NAME="DSPDemo_0.2.0.dmg"

python3.7 setup.py py2app --plist=scripts/info.plist

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
awk '{gsub("@executable_path/../Frameworks/Python.framework/Versions/2.7/Python", "@executable_path/../Frameworks/Python.framework/Versions/3.7/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk '{gsub("Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7", "@executable_path/../Frameworks/Python.framework/Versions/3.7/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk '{gsub("/usr/local/bin/python3.7", "@executable_path/../Frameworks/Python.framework/Versions/3.7/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist

install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_core.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_core.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_core.so
install_name_tool -change @loader_path/libwx_osx_cocoau_adv-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_adv-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_osx_cocoau_html-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_html-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_osx_cocoau_stc-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_stc-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_baseu_xml-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_xml-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/siplib.so
install_name_tool -change @loader_path/libwx_baseu_net-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/siplib.so
install_name_tool -change @loader_path/libwx_baseu-3.0.0.4.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.0.0.4.0.dylib Resources/lib/python3.7/lib-dynload/wx/siplib.so

install_name_tool -change @loader_path/libportaudio.2.dylib @loader_path/../../../../../Frameworks/libportaudio.2.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libportmidi.dylib @loader_path/../../../../../Frameworks/libportmidi.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/liblo.7.dylib @loader_path/../../../../../Frameworks/liblo.7.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libsndfile.1.dylib @loader_path/../../../../../Frameworks/libsndfile.1.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libportaudio.2.dylib @loader_path/../../../../../Frameworks/libportaudio.2.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/libportmidi.dylib @loader_path/../../../../../Frameworks/libportmidi.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/liblo.7.dylib @loader_path/../../../../../Frameworks/liblo.7.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/libsndfile.1.dylib @loader_path/../../../../../Frameworks/libsndfile.1.dylib Resources/lib/python3.7/lib-dynload/pyo/_pyo64.so

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
