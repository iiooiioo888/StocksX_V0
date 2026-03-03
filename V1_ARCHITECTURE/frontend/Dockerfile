# Frontend Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 複製 package 文件
COPY package*.json ./

# 安裝依賴
RUN npm install

# 複製原始碼
COPY . .

# 建立生產版本
RUN npm run build

# 生產階段
FROM nginx:alpine

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 複製建立的檔案
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
