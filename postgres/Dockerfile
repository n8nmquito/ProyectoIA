FROM postgres:16-bookworm

COPY init-databases.sh /docker-entrypoint-initdb.d/10-init-databases.sh
RUN sed -i 's/\r$//' /docker-entrypoint-initdb.d/10-init-databases.sh \
    && chmod 755 /docker-entrypoint-initdb.d/10-init-databases.sh
