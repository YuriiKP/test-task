FROM postgres:12.2

COPY docker-entrypoint-initdb.d /docker-entrypoint-initdb.d/

RUN sed -i -e 's/\r$//' docker-entrypoint-initdb.d/adventureworks_restore.sh