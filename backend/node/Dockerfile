FROM node:20-slim

WORKDIR /app

# Install dependencies first (layer-cache friendly)
COPY package.json .
RUN npm install --omit=dev

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
