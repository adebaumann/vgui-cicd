FROM python:3.13-slim AS baustelle
RUN mkdir /app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --proxy http://proxy-bvcol.admin.ch:8080  --upgrade pip
COPY requirements.txt /app/
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --proxy http://proxy-bvcol.admin.ch:8080  --no-cache-dir -r requirements.txt

FROM python:3.13-slim
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

COPY --from=baustelle /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=baustelle /usr/local/bin/ /usr/local/bin/
RUN rm /usr/bin/tar
RUN rm /usr/lib/x86_64-linux-gnu/libncur*
WORKDIR /app
COPY --chown=appuser:appuser . .
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
USER appuser
EXPOSE 8000
CMD ["gunicorn","--bind","0.0.0.0:8000","--workers","3","VorgabenUI.wsgi:application"]

