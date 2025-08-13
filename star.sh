echo "啟動 AHEAD Take Home Project..."

if ! docker info > /dev/null 2>&1; then
    echo "Docker 未運行，請先啟動 Docker"
    exit 1
fi

mkdir -p uploads
mkdir -p logs

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 檔案，請創建檔案"
    exit 1
fi


echo "啟動 Docker 服務..."
docker-compose up -d


echo "API 服務: http://localhost:8000"
echo "API 文檔: http://localhost:8000/docs"
echo "資料庫: localhost:5432"
echo "Redis: localhost:6379"

