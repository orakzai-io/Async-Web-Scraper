# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# Production Stage (NGINX)
FROM nginx:alpine

# Copy built assets from the build stage to NGINX standard directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a custom NGINX configuration (if caching or reroutes are needed)
# Or rely on defaults since it's a simple dashboard
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
