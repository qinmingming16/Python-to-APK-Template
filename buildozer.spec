[app]
#标题允许中文
title = MAGILM
package.name = magilm
package.domain = io.github.qinmingming16

#工作目录
source.dir = .
#需要打包的文件类型
source.include_exts = py,png,jpg,kv,atlas,otf,xml,wav

version = 0.1
#依赖库
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,kivymd==1.1.1

source.exclude_exts = spec
source.exclude_dirs = venv,bin

android.add_res = src/main/res
android.add_manifest = src/main/AndroidManifest.xml
android.add_src = src/main/java
android.add_assets = fonts/,audio/

android.services = AccessibilityKeyMonitorService:io.github.qinmingming16.magilm.accessibility.AccessibilityKeyMonitorService

android.wakelock = True
android.proguard = False

icon.filename = icon.png
#presplash.filename = presplash.png
fullscreen = 0
orientation = portrait

#不要改动
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.ndk = 25b
exclude_patterns = **/test/*, **/tests/*
android.gradle_download = https://services.gradle.org/distributions/gradle-7.6.4-all.zip
android.gradle_plugin = 7.4.2
android.sdk = 33
android.ndk_api = 21
p4a.bootstrap = sdl2

#打包需要网络权限
android.permissions = INTERNET

#以下为release模式需要，debug无需启用
#android.keystore = 
#android.keystore_storepass = 
#android.keystore_keypass = 
#android.keystore_alias = 

[buildozer]
log_level = 2
warn_on_root = 1
