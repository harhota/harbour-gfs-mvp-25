FROM node:18

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# Build
RUN npm run build

# Serve using Vite preview
EXPOSE 5173
CMD ["npx", "vite", "preview", "--port", "5173", "--host"]
