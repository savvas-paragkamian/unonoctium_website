# Single-stage: serve pre-built Hugo output with nginx.
# Build the site first with: make build
# Then build this image with: make container
FROM nginx:1.27-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public/ /usr/share/nginx/html

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
