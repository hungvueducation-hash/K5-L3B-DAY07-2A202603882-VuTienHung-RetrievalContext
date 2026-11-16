#!/bin/sh
# Tải PDF gốc (CC BY-NC 3.0 IGO) từ World Bank Open Knowledge Repository, kiểm tra SHA-256.
curl -sL -A "Mozilla/5.0" -o vietnam_rising_en.pdf "https://openknowledge.worldbank.org/server/api/core/bitstreams/90e02c2a-6320-45c6-a99f-c8f506db24d5/content"
echo "e2974ce54d5e554cc10911298b200cad2c842e1b74fc436f78186e508b01c552  vietnam_rising_en.pdf" | sha256sum -c -
