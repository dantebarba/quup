# Comandos Útiles - Plex AI Curator

## 🚀 Inicio Rápido

### Configuración Inicial
```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar configuración (reemplazar con tus credenciales reales)
nano .env  # o vim, code, etc.
```

### Desarrollo Local
```bash
# Crear entorno virtual
python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# En otra terminal - verificar
curl http://localhost:8000/health
```

### Docker
```bash
# Construir imagen
docker build -t plex-ai-curator:latest .

# Ejecutar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down

# Reconstruir después de cambios
docker-compose up -d --build
```

---

## 🧪 Testing

### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con verbose
pytest -v

# Con cobertura
pytest --cov=app tests/

# Test específico
pytest tests/test_integration.py::test_health_endpoint -v

# Con output detallado
pytest -v -s
```

### Verificar Calidad del Código
```bash
# Type checking (requiere mypy)
pip install mypy
mypy app/

# Linting (requiere pylint)
pip install pylint
pylint app/

# Format check (requiere black)
pip install black
black --check app/ tests/
```

---

## 📡 Uso de la API

### Health Check
```bash
curl http://localhost:8000/health
```

### Información General
```bash
curl http://localhost:8000/
```

### Sincronizar Biblioteca (Requiere Token)
```bash
# Formato básico
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: YOUR_TOKEN_HERE"

# Con respuesta formateada
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: YOUR_TOKEN_HERE" | python -m json.tool
```

### Generar Recomendaciones (Requiere Token)
```bash
# Modo síncrono (espera respuesta)
curl -X POST http://localhost:8000/recommend \
  -H "x-api-token: YOUR_TOKEN_HERE" | python -m json.tool

# Modo asíncrono (proceso en background)
curl -X POST "http://localhost:8000/recommend?async_mode=true" \
  -H "x-api-token: YOUR_TOKEN_HERE" | python -m json.tool
```

### Testing de Autenticación
```bash
# Sin token (debe fallar)
curl -X POST http://localhost:8000/sync

# Con token incorrecto (debe fallar)
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: wrong-token"

# Con token correcto (debe funcionar)
curl -X POST http://localhost:8000/sync \
  -H "x-api-token: YOUR_TOKEN_HERE"
```

---

## 🐳 Docker - Comandos Avanzados

### Gestión de Contenedores
```bash
# Ver contenedores en ejecución
docker ps

# Ver todos los contenedores
docker ps -a

# Logs en tiempo real
docker logs -f plex-ai-curator

# Entrar al contenedor
docker exec -it plex-ai-curator /bin/bash

# Ver uso de recursos
docker stats plex-ai-curator

# Reiniciar contenedor
docker restart plex-ai-curator
```

### Gestión de Imágenes
```bash
# Listar imágenes
docker images

# Eliminar imagen antigua
docker rmi plex-ai-curator:latest

# Limpiar imágenes no usadas
docker image prune -a

# Ver tamaño de imagen
docker images plex-ai-curator
```

### Docker Compose - Avanzado
```bash
# Ver configuración
docker-compose config

# Escalar (si fuera necesario)
docker-compose up -d --scale plex-ai-curator=2

# Recrear contenedores
docker-compose up -d --force-recreate

# Eliminar todo (contenedores, redes, volúmenes)
docker-compose down -v
```

---

## 🔍 Debugging

### Ver Logs de la Aplicación
```bash
# Desarrollo local
tail -f app.log  # Si configuras file logging

# Docker
docker logs plex-ai-curator
docker logs -f plex-ai-curator --tail 100

# Docker Compose
docker-compose logs
docker-compose logs -f --tail 100
```

### Verificar Conectividad
```bash
# Verificar si Plex es accesible
curl -I http://YOUR_PLEX_URL:32400

# Verificar si OpenAI es accesible
curl -I https://api.openai.com

# Verificar si Telegram es accesible (si está habilitado)
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### Inspeccionar Estado
```bash
# Ver variables de entorno en contenedor
docker exec plex-ai-curator env | grep PLEX
docker exec plex-ai-curator env | grep OPENAI

# Ver archivos en contenedor
docker exec plex-ai-curator ls -la /app
docker exec plex-ai-curator ls -la /app/samples
```

---

## 📊 Monitoreo

### Health Checks
```bash
# Script de monitoreo simple
watch -n 5 'curl -s http://localhost:8000/health | python -m json.tool'

# Con notificación si falla
while true; do
  if ! curl -sf http://localhost:8000/health > /dev/null; then
    echo "⚠️  Servicio caído!" | mail -s "Alert" your@email.com
  fi
  sleep 60
done
```

### Métricas Básicas
```bash
# Tiempo de respuesta
time curl -s http://localhost:8000/health

# Requests por segundo (requiere apache bench)
ab -n 1000 -c 10 http://localhost:8000/health

# Uso de memoria del contenedor
docker stats plex-ai-curator --no-stream
```

---

## 🔧 Mantenimiento

### Actualizar Dependencias
```bash
# Ver dependencias desactualizadas
pip list --outdated

# Actualizar todas
pip install -U -r requirements.txt

# Regenerar requirements.txt
pip freeze > requirements.txt
```

### Backup
```bash
# Backup de configuración
cp .env .env.backup.$(date +%Y%m%d)

# Backup de base de datos (si aplica)
docker exec plex-ai-curator tar czf /backup.tar.gz /app/data
docker cp plex-ai-curator:/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

### Limpieza
```bash
# Limpiar caché de Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Limpiar Docker
docker system prune -a
docker volume prune

# Limpiar tests
rm -rf .pytest_cache htmlcov .coverage
```

---

## 🌐 Producción

### Deploy a Servidor Remoto
```bash
# SSH y setup
ssh user@server
git clone <repo-url>
cd quup

# Configurar
cp .env.example .env
nano .env  # Editar con credenciales de producción

# Ejecutar
docker-compose up -d

# Verificar
curl http://localhost:8000/health
```

### Configurar como Servicio (systemd)
```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/plex-ai-curator.service

# Contenido:
[Unit]
Description=Plex AI Curator
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/quup
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target

# Habilitar y iniciar
sudo systemctl enable plex-ai-curator
sudo systemctl start plex-ai-curator
sudo systemctl status plex-ai-curator
```

### Logs de Producción
```bash
# Configurar log rotation
sudo nano /etc/logrotate.d/plex-ai-curator

# Contenido:
/var/log/plex-ai-curator/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

---

## 🆘 Solución de Problemas

### Problemas Comunes

#### "Cannot connect to Plex server"
```bash
# Verificar conectividad
ping YOUR_PLEX_HOST
curl -I http://YOUR_PLEX_URL:32400

# Verificar token
curl http://YOUR_PLEX_URL:32400/library/sections?X-Plex-Token=YOUR_TOKEN
```

#### "OpenAI API error"
```bash
# Verificar clave API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_OPENAI_KEY"

# Verificar créditos (via web)
# https://platform.openai.com/account/usage
```

#### "Tests failing"
```bash
# Reinstalar dependencias limpias
pip install --upgrade --force-reinstall -r requirements.txt

# Verificar Python version
python --version  # Debe ser 3.12+

# Limpiar caché
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .pytest_cache
```

#### "Docker build fails"
```bash
# Limpiar todo Docker
docker system prune -a

# Reconstruir sin caché
docker build --no-cache -t plex-ai-curator:latest .

# Verificar espacio en disco
df -h
```

---

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Plex API Documentation](https://python-plexapi.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Nota:** Reemplaza `YOUR_TOKEN_HERE`, `YOUR_PLEX_URL`, etc. con tus valores reales de configuración.
