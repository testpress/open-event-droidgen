#!/bin/bash
# Install Android SDK
wget --output-document=/opt/android-sdk.zip https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip
unzip /opt/android-sdk.zip -d /opt/android-sdk-linux
rm -f /opt/android-sdk.zip
mkdir /opt/android-sdk-linux/platform-tools
chown -R $(whoami):$(whoami) /opt/android-sdk-linux
/opt/tools/android-accept-licenses.sh "/opt/android-sdk-linux/tools/android update sdk --all --no-ui --filter --use-sdk-wrapper platform-tools,tools"
/opt/tools/android-accept-licenses.sh "/opt/android-sdk-linux/tools/android update sdk --all --no-ui --filter --use-sdk-wrapper platform-tools,tools,build-tools-27.0.3,android-27,extra-android-support,extra-android-m2repository,extra-google-m2repository,extra-google-google_play_services"
