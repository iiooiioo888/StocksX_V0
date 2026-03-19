#!/bin/bash

# ════════════════════════════════════════════════════════════
# StocksX 一键部署脚本
# ════════════════════════════════════════════════════════════

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ════════════════════════════════════════════════════════════
# 检查前置条件
# ════════════════════════════════════════════════════════════
check_prerequisites() {
    log_info "检查前置条件..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装"
        exit 1
    fi
    
    log_success "前置条件检查通过"
}

# ════════════════════════════════════════════════════════════
# 创建必要目录
# ════════════════════════════════════════════════════════════
setup_directories() {
    log_info "创建必要目录..."
    
    mkdir -p data logs monitoring/grafana/dashboards
    
    log_success "目录创建完成"
}

# ════════════════════════════════════════════════════════════
# 配置环境变量
# ════════════════════════════════════════════════════════════
setup_environment() {
    log_info "配置环境变量..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        log_warning "已创建 .env 文件，请根据实际情况修改配置"
    fi
    
    log_success "环境变量配置完成"
}

# ════════════════════════════════════════════════════════════
# 构建 Docker 镜像
# ════════════════════════════════════════════════════════════
build_images() {
    log_info "构建 Docker 镜像..."
    
    docker-compose build
    
    log_success "镜像构建完成"
}

# ════════════════════════════════════════════════════════════
# 启动服务
# ════════════════════════════════════════════════════════════
start_services() {
    log_info "启动服务..."
    
    docker-compose up -d
    
    log_success "服务启动完成"
    
    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 10
    
    # 检查服务状态
    docker-compose ps
}

# ════════════════════════════════════════════════════════════
# 显示访问信息
# ════════════════════════════════════════════════════════════
show_access_info() {
    echo ""
    log_success "═══════════════════════════════════════════════"
    log_success "  StocksX 部署完成！"
    log_success "═══════════════════════════════════════════════"
    echo ""
    log_info "应用访问地址：http://localhost:8501"
    log_info "WebSocket 地址：ws://localhost:8001/ws"
    log_info "Redis: localhost:6379"
    log_info "Prometheus: http://localhost:9090"
    log_info "Grafana: http://localhost:3000 (admin/admin123)"
    echo ""
    log_info "查看日志：docker-compose logs -f"
    log_info "停止服务：docker-compose down"
    log_info "重启服务：docker-compose restart"
    echo ""
}

# ════════════════════════════════════════════════════════════
# 主函数
# ════════════════════════════════════════════════════════════
main() {
    echo ""
    log_info "═══════════════════════════════════════════════"
    log_info "  StocksX 一键部署脚本"
    log_info "═══════════════════════════════════════════════"
    echo ""
    
    check_prerequisites
    setup_directories
    setup_environment
    build_images
    start_services
    show_access_info
}

# 执行主函数
main "$@"
