FROM nginx:1.27-alpine
RUN apk --no-cache upgrade
COPY index.html /usr/share/nginx/html/index.html
COPY config.js /usr/share/nginx/html/config.js

EXPOSE 80
