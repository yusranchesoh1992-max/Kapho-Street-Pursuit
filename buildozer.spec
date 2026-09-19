[app]

title = Kapho Street Pursuit
package.name = kaphostreetpursuit
package.domain = org.kapho

source.dir = .
source.main = main.py

source.include_exts = py,png,jpg,jpeg,ttf,ogg,wav

version = 1.0

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.permissions = VIBRATE


[buildozer]

log_level = 2
warn_on_root = 1
