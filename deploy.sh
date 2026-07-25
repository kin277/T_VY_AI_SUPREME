#!/bin/bash
echo "🚀 BẮT ĐẦU TRIỂN KHAI"
git pull origin main
docker-compose build
docker-compose down
docker-compose up -d
echo "✅ TRIỂN KHAI HOÀN TẤT!"