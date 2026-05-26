# Despliegue en AWS

Guía paso a paso para llevar el proyecto a producción en AWS. El orden importa: Cognito y S3 primero, luego RDS, luego EC2, y finalmente el frontend.

---

## Tabla de contenidos

- [Prerrequisitos](#prerrequisitos)
- [1. AWS Cognito (autenticación)](#1-aws-cognito-autenticación)
- [2. AWS S3 (almacenamiento de archivos)](#2-aws-s3-almacenamiento-de-archivos)
- [3. AWS RDS — PostgreSQL con pgvector](#3-aws-rds--postgresql-con-pgvector)
- [4. AWS EC2 — Backend + Ollama](#4-aws-ec2--backend--ollama)
- [5. HTTPS con Let's Encrypt (Nginx + Certbot)](#5-https-con-lets-encrypt-nginx--certbot)
- [6. AWS S3 + CloudFront — Frontend](#6-aws-s3--cloudfront--frontend)
- [7. Variables de entorno de producción](#7-variables-de-entorno-de-producción)
- [8. Verificación final](#8-verificación-final)

---

## Prerrequisitos

- Cuenta de AWS con permisos de administrador (o políticas específicas para EC2, RDS, S3, Cognito, CloudFront).
- AWS CLI instalada y configurada (`aws configure`).
- Dominio propio (puede ser un subdominio gratuito de DuckDNS si no tienes dominio).
- Claves SSH para conectarte a EC2.

---

## 1. AWS Cognito (autenticación)

### 1.1 Crear el User Pool

```bash
aws cognito-idp create-user-pool \
  --pool-name agente-gastronomia \
  --policies '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}' \
  --auto-verified-attributes email \
  --username-attributes email \
  --region us-east-1
```

Anota el `UserPoolId` de la respuesta.

### 1.2 Crear el App Client (sin secreto, para PKCE desde el frontend)

```bash
aws cognito-idp create-user-pool-client \
  --user-pool-id <UserPoolId> \
  --client-name agente-frontend \
  --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --supported-identity-providers COGNITO \
  --callback-urls '["https://TU_DOMINIO/callback"]' \
  --logout-urls '["https://TU_DOMINIO/login"]' \
  --allowed-o-auth-flows code \
  --allowed-o-auth-scopes openid email profile \
  --allowed-o-auth-flows-user-pool-client \
  --region us-east-1
```

Anota el `ClientId`.

### 1.3 Configurar el dominio del Hosted UI

```bash
aws cognito-idp create-user-pool-domain \
  --domain agente-gastronomia-SUFIJO_UNICO \
  --user-pool-id <UserPoolId> \
  --region us-east-1
```

El Hosted UI quedará en: `https://agente-gastronomia-SUFIJO_UNICO.auth.us-east-1.amazoncognito.com`

> **Opcional:** Para añadir Google como proveedor de identidad, crea un OAuth2 Client en Google Cloud Console y regístralo como Identity Provider en el User Pool desde la consola de AWS.

---

## 2. AWS S3 (almacenamiento de archivos)

### 2.1 Crear el bucket de documentos

```bash
aws s3api create-bucket \
  --bucket agente-gastronomia-docs-SUFIJO_UNICO \
  --region us-east-1

# Bloquear acceso público (los archivos solo los lee el backend con credenciales IAM)
aws s3api put-public-access-block \
  --bucket agente-gastronomia-docs-SUFIJO_UNICO \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2.2 Crear el usuario IAM para el backend

```bash
aws iam create-user --user-name agente-backend-s3

aws iam put-user-policy \
  --user-name agente-backend-s3 \
  --policy-name s3-access \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Action":["s3:PutObject","s3:GetObject","s3:DeleteObject"],
      "Resource":"arn:aws:s3:::agente-gastronomia-docs-SUFIJO_UNICO/*"
    }]
  }'

# Crear clave de acceso
aws iam create-access-key --user-name agente-backend-s3
```

Guarda `AccessKeyId` y `SecretAccessKey`.

---

## 3. AWS RDS — PostgreSQL con pgvector

### 3.1 Crear el Security Group de la BD

```bash
# Obtén el ID de la VPC por defecto
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text)

aws ec2 create-security-group \
  --group-name agente-rds-sg \
  --description "RDS PostgreSQL para agente RAG" \
  --vpc-id $VPC_ID
```

Anota el `GroupId`. El acceso al puerto 5432 solo se abrirá desde el Security Group de EC2 (se configura en el paso 4).

### 3.2 Crear la instancia RDS

```bash
aws rds create-db-instance \
  --db-instance-identifier agente-gastronomia-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.3 \
  --master-username agente_user \
  --master-user-password "TU_CONTRASENA_SEGURA" \
  --db-name agente_db \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids <RDS_GroupId> \
  --no-publicly-accessible \
  --region us-east-1
```

La creación tarda ~5 minutos. Obtén el endpoint cuando esté disponible:

```bash
aws rds describe-db-instances \
  --db-instance-identifier agente-gastronomia-db \
  --query "DBInstances[0].Endpoint.Address" --output text
```

### 3.3 Habilitar pgvector

Una vez que la instancia esté `available`, conéctate desde EC2 y ejecuta:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

Las migraciones de Alembic crearán el resto del esquema automáticamente al arrancar el backend.

---

## 4. AWS EC2 — Backend + Ollama

### 4.1 Crear el Security Group de EC2

```bash
SG_EC2=$(aws ec2 create-security-group \
  --group-name agente-ec2-sg \
  --description "Backend FastAPI + Ollama" \
  --vpc-id $VPC_ID \
  --query "GroupId" --output text)

# SSH (restringe a tu IP en producción real)
aws ec2 authorize-security-group-ingress --group-id $SG_EC2 \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

# HTTP y HTTPS (tráfico web)
aws ec2 authorize-security-group-ingress --group-id $SG_EC2 \
  --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $SG_EC2 \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# Permitir que EC2 acceda a RDS
aws ec2 authorize-security-group-ingress \
  --group-id <RDS_GroupId> \
  --protocol tcp --port 5432 \
  --source-group $SG_EC2
```

### 4.2 Lanzar la instancia

```bash
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t3.xlarge \
  --key-name TU_KEY_PAIR \
  --security-group-ids $SG_EC2 \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=agente-backend}]' \
  --region us-east-1
```

> Se recomienda `t3.xlarge` (4 vCPU, 16 GB RAM) para correr Llama 3.2 3B en CPU con latencia razonable. Con `t3.large` funciona pero lento.

### 4.3 Configurar el servidor

Conéctate por SSH y ejecuta:

```bash
# Actualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu
newgrp docker

# Instalar Docker Compose plugin
sudo apt-get install -y docker-compose-plugin

# Clonar el repositorio
git clone https://github.com/Masiori/ProyectoRagImplementacion.git
cd ProyectoRagImplementacion

# Crear el .env de producción
cp .env.example .env
nano .env   # rellenar con los valores reales (ver sección 7)

# Levantar solo postgres + ollama + backend (sin frontend)
docker compose up -d postgres ollama backend

# Descargar el modelo (solo la primera vez, ~5 min)
docker exec -it agente-ollama ollama pull llama3.2:3b
```

### 4.4 Verificar que el backend responde

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
curl http://localhost:8000/health/ollama
```

---

## 5. HTTPS con Let's Encrypt (Nginx + Certbot)

### 5.1 Instalar Nginx y Certbot

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 5.2 Configurar Nginx como reverse proxy

```bash
sudo nano /etc/nginx/sites-available/agente
```

Pega esta configuración (reemplaza `TU_DOMINIO`):

```nginx
server {
    listen 80;
    server_name TU_DOMINIO;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;    # necesario para llamadas lentas a Ollama
        proxy_send_timeout 120s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/agente /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5.3 Obtener el certificado SSL

```bash
sudo certbot --nginx -d TU_DOMINIO
```

Certbot modifica el bloque `server` para añadir SSL y configura la renovación automática.

---

## 6. AWS S3 + CloudFront — Frontend

### 6.1 Build del frontend

En tu máquina local:

```bash
cd frontend

# Crear .env de producción
cat > .env.production << EOF
VITE_API_URL=https://TU_DOMINIO
VITE_COGNITO_DOMAIN=agente-gastronomia-SUFIJO_UNICO.auth.us-east-1.amazoncognito.com
VITE_COGNITO_CLIENT_ID=<ClientId>
VITE_COGNITO_REDIRECT_URI=https://TU_FRONTEND_DOMINIO/callback
VITE_COGNITO_LOGOUT_URI=https://TU_FRONTEND_DOMINIO/login
EOF

npm run build
```

### 6.2 Crear el bucket del frontend y subir los archivos

```bash
# Crear bucket
aws s3api create-bucket \
  --bucket agente-gastronomia-frontend \
  --region us-east-1

# Habilitar hosting estático
aws s3 website s3://agente-gastronomia-frontend \
  --index-document index.html \
  --error-document index.html

# Subir el build
aws s3 sync frontend/dist/ s3://agente-gastronomia-frontend --delete
```

### 6.3 Crear la distribución CloudFront

Desde la consola de AWS (GUI recomendada para este paso):

1. Ve a **CloudFront → Create distribution**.
2. Origin domain: selecciona el bucket S3.
3. Viewer protocol policy: **Redirect HTTP to HTTPS**.
4. Default root object: `index.html`.
5. En **Error pages**, añade: HTTP error code `403` → Response page `/index.html` → HTTP 200. Esto permite que React Router maneje las rutas del lado del cliente.
6. Crea la distribución y anota el dominio `*.cloudfront.net`.

### 6.4 Dominio personalizado (opcional)

Si tienes un dominio en Route 53, añade un registro CNAME apuntando al dominio de CloudFront y configura un certificado ACM en la distribución.

---

## 7. Variables de entorno de producción

Copia `.env.example` en EC2 y rellena estos valores:

```env
# Aplicación
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# Base de datos (RDS)
DATABASE_URL=postgresql+asyncpg://agente_user:TU_CONTRASENA@<RDS_ENDPOINT>:5432/agente_db
POSTGRES_USER=agente_user
POSTGRES_PASSWORD=TU_CONTRASENA
POSTGRES_DB=agente_db

# Ollama (mismo host, dentro de Docker)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT_SECONDS=90

# RAG
SIMILARITY_THRESHOLD=0.70
TOP_K=5

# AWS Cognito
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=<UserPoolId>
COGNITO_APP_CLIENT_ID=<ClientId>

# AWS S3
AWS_REGION=us-east-1
AWS_S3_BUCKET=agente-gastronomia-docs-SUFIJO_UNICO
AWS_ACCESS_KEY_ID=<AccessKeyId>
AWS_SECRET_ACCESS_KEY=<SecretAccessKey>

# CORS (dominio del frontend en CloudFront o personalizado)
CORS_ORIGINS=https://TU_FRONTEND_DOMINIO
```

---

## 8. Verificación final

Una vez desplegado todo, verifica cada capa:

```bash
# Backend operativo con HTTPS
curl https://TU_DOMINIO/health
curl https://TU_DOMINIO/health/db
curl https://TU_DOMINIO/health/pgvector
curl https://TU_DOMINIO/health/ollama

# Frontend cargando (desde el navegador)
# → https://TU_FRONTEND_DOMINIO
#   Debe mostrar la página de login de Cognito al hacer clic en "Iniciar sesión"

# Flujo completo de prueba
# 1. Iniciar sesión con un usuario de Cognito
# 2. Subir un documento PDF desde la página de Documentos
# 3. Esperar a que el status cambie a "ready" (polling automático)
# 4. Ir al Chat y hacer una pregunta relacionada con el documento
# 5. Verificar que la respuesta incluye fuentes
```

### Comandos de mantenimiento en EC2

```bash
# Ver logs del backend en producción
docker compose logs -f backend

# Actualizar el código
git pull
docker compose build backend
docker compose up -d backend

# Renovar certificado SSL (automático con cron, pero puedes forzarlo)
sudo certbot renew --dry-run
```