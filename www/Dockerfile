# Page d'accueil bibliofelia.org. Contexte de build = racine du dépôt.
FROM nginx:1.27-alpine
COPY www/nginx.conf /etc/nginx/conf.d/default.conf
COPY www/index.html /usr/share/nginx/html/index.html
COPY static/fonts/bricolage-grotesque-3.woff2 /usr/share/nginx/html/fonts/bricolage.woff2
COPY static/fonts/dm-sans-2.woff2 /usr/share/nginx/html/fonts/dm-sans.woff2
COPY static/img/ofelia-logo.png /usr/share/nginx/html/img/ofelia-logo.png
COPY static/img/ofelia-logo-small.png /usr/share/nginx/html/img/ofelia-logo-small.png
COPY www/media/ofelia-home.mp4 /usr/share/nginx/html/media/ofelia-home.mp4
COPY www/media/ofelia-home-poster.jpg /usr/share/nginx/html/media/ofelia-home-poster.jpg
