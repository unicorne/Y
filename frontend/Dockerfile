FROM nginx:alpine

# Copy the static files to the nginx html directory
COPY public/ /usr/share/nginx/html/

# Copy the nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]