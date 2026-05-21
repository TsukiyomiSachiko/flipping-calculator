# Build Stage
FROM node:20-slim as build

WORKDIR /app

# Accept the PAT build argument
ARG THEME_REPO_PAT

# Install git (required for cloning github npm dependencies) and configure it
RUN apt-get update && apt-get install -y git && \
    git config --global url."https://${THEME_REPO_PAT}@github.com/".insteadOf "https://github.com/"

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build for production
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
