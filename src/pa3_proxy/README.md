# Proxy
This container is needed for creating letsencrypt certificates.

It consists of a nginx container, redirecting port 80 traffic not for letsencrypt to the frontend.

Currently, the container has to be manually used via `docker exec -it pa3_proxy bash`, 
to execute letsencrypt, or frequently restarted/redeployed.