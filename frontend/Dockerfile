# Stage 1: Build the Angular SSR application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json and package-lock.json first for caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the SSR application
RUN npm run build

# Stage 2: Serve the application
FROM node:20-alpine

WORKDIR /app

# Copy the built artifacts from the build stage
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./package.json

# Expose the port (Angular SSR default is usually 4000)
EXPOSE 4000

# Start the SSR server
CMD ["npm", "run", "serve:ssr"]
