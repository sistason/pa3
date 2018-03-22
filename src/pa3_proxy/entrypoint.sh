

if [[ $1 == "/bin/bash" || $1 == "bash" ]]; then 
    exec "$@"
else
    server_url=$1
    letsencrypt certonly --webroot --webroot-path /usr/share/nginx/html/ --agree-tos --email pa@$server_url -n -d $server_url
    nginx -g "daemon off;"
fi
