FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --production

COPY app.js ./

# Config directory for persisted state
RUN mkdir -p /app/config

EXPOSE 3330

CMD ["node", "app.js"]
