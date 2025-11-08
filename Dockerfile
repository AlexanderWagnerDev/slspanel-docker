FROM alexanderwagnerdev/alpine:builder as builder

RUN apk update && \
    apk upgrade && \
    apk add --no-cache python3 py3-pip bash gettext tzdata && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY . .

RUN python3 -m venv /venv

RUN /bin/sh -c "source /venv/bin/activate && pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && python3 manage.py compilemessages && python3 manage.py collectstatic --noinput && python3 manage.py makemigrations streams"

ENV PATH="/venv/bin:$PATH"

FROM alexanderwagnerdev/alpine:autoupdate-stable

RUN apk update && \
    apk upgrade && \
    apk add --no-cache python3 py3-pip bash tzdata && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY --from=builder /app/slspanel /app/slspanel
COPY --from=builder /app/streams /app/streams
COPY --from=builder /app/templates /app/templates
COPY --from=builder /app/locale /app/locale
COPY --from=builder /app/static /app/static
COPY --from=builder /app/staticfiles /app/staticfiles
COPY --from=builder /app/manage.py /app/manage.py
COPY --from=builder /venv /venv

ENV PATH="/venv/bin:$PATH"

EXPOSE 8000/tcp

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]