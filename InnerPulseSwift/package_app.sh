#!/bin/bash

APP_NAME="InnerPulseSwift"
APP_BUNDLE="${APP_NAME}.app"
BUILD_DIR=".build/debug"
ICON_SOURCE="InnerPulseApp/Resources/InnerPulse.icns"

echo "Building ${APP_NAME}..."
swift build --disable-sandbox

if [ $? -ne 0 ]; then
    echo "Build failed."
    exit 1
fi

echo "Creating ${APP_BUNDLE}..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

echo "Copying executable..."
cp "${BUILD_DIR}/InnerPulseApp" "${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"

echo "Copying resources..."
if [ -f "${ICON_SOURCE}" ]; then
    cp "${ICON_SOURCE}" "${APP_BUNDLE}/Contents/Resources/AppIcon.icns"
else
    echo "Warning: Icon not found at ${ICON_SOURCE}"
fi

echo "Creating Info.plist..."
cat > "${APP_BUNDLE}/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.rikuogura.${APP_NAME}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
EOF

echo "${APP_BUNDLE} created successfully!"
