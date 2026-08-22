# Frontend. Two targets: `dev` runs Vite with hot reload (used by compose),
# `production` builds static assets and serves them with nginx.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# --- development ---
FROM deps AS dev
COPY . .
EXPOSE 5173
# --host 0.0.0.0 so the server is reachable from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# --- production ---
FROM deps AS build
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
