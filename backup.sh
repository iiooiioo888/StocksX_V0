#!/bin/bash
# ════════════════════════════════════════════════════════════
# StocksX V0 - 备份脚本
# 用途：备份数据库和重要文件
# 用法：./backup.sh
# ════════════════════════════════════════════════════════════

set -e

# 配置
BACKUP_DIR="/opt/stocksx/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}StocksX V0 - 备份脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR/db"
mkdir -p "$BACKUP_DIR/files"

# ════════════════════════════════════════════════════════════
# 1. 备份数据库
# ════════════════════════════════════════════════════════════
echo -e "${YELLOW}[1/3] 备份 PostgreSQL 数据库...${NC}"

docker compose exec -T postgres pg_dump -U stocksx_user stocksx > "$BACKUP_DIR/db/stocksx_$DATE.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库备份成功：$BACKUP_DIR/db/stocksx_$DATE.sql${NC}"
    # 压缩备份
    gzip "$BACKUP_DIR/db/stocksx_$DATE.sql"
    echo -e "${GREEN}✓ 数据库备份已压缩：$BACKUP_DIR/db/stocksx_$DATE.sql.gz${NC}"
else
    echo -e "${RED}✗ 数据库备份失败${NC}"
    exit 1
fi

# ════════════════════════════════════════════════════════════
# 2. 备份重要文件
# ════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[2/3] 备份重要文件...${NC}"

# 备份 .env 文件
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/files/env_$DATE"
    echo -e "${GREEN}✓ .env 文件已备份${NC}"
fi

# 备份模型文件
if [ -d "models" ] && [ "$(ls -A models 2>/dev/null)" ]; then
    tar -czf "$BACKUP_DIR/files/models_$DATE.tar.gz" models/
    echo -e "${GREEN}✓ 模型文件已备份${NC}"
fi

# 备份日志（最近 7 天）
if [ -d "logs" ]; then
    find logs -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/files/logs_$DATE.tar.gz" {} + 2>/dev/null || true
    echo -e "${GREEN}✓ 日志文件已备份（最近 7 天）${NC}"
fi

# ════════════════════════════════════════════════════════════
# 3. 清理旧备份
# ════════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}[3/3] 清理旧备份（保留最近 $RETENTION_DAYS 天）...${NC}"

find "$BACKUP_DIR/db" -name "stocksx_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/files" -name "*_$DATE.*" -mtime +$RETENTION_DAYS -delete

echo -e "${GREEN}✓ 旧备份已清理${NC}"

# ════════════════════════════════════════════════════════════
# 完成
# ════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}备份完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "备份位置：$BACKUP_DIR"
echo ""
echo "数据库备份：$BACKUP_DIR/db/stocksx_$DATE.sql.gz"
echo "文件备份：$BACKUP_DIR/files/"
echo ""

# 显示备份大小
echo "备份大小："
du -sh "$BACKUP_DIR" 2>/dev/null || true
