FROM node:18-alpine AS build

WORKDIR /app

# Copier package.json et installer les dépendances
COPY package*.json ./
RUN npm ci

# Copier le code source et builder
COPY . .
RUN npm run build

# Stage 2: Nginx pour servir l'application
FROM nginx:alpine

# Copier le build depuis le stage précédent
COPY --from=build /app/dist /usr/share/nginx/html

# Copier la configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
