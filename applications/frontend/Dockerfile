FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY src ./src

RUN npm run build

EXPOSE 80

CMD ["sh", "-c", "npx http-server dist -p 80"]
