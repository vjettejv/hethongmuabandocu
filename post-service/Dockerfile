FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Keep uploads persistent via volume
VOLUME ["/app/uploads"]
EXPOSE 3003
CMD ["npm", "start"]
