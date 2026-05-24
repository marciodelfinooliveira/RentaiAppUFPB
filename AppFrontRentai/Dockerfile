FROM node:22-bookworm AS builder

WORKDIR /app

ARG VITE_API_BASE_URL_ARG
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL_ARG}

COPY package.json package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

COPY . .
RUN npm run build

FROM nginx:stable-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
