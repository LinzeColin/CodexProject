FROM nginx:1.27-alpine
RUN apk upgrade --no-cache          # 安全基线: 基底补丁(Trivy 实测可清零 HIGH/CRIT)
COPY public /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
