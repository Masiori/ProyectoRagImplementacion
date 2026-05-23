# Infraestructura

> **Estado actual:** Milestone 1 — aún sin contenido.
>
> Esta carpeta contendrá los scripts y notas para desplegar el proyecto en AWS durante el **Milestone 7**.

---

## Recursos AWS previstos

| Recurso | Propósito | Milestone |
|---|---|---|
| **Cognito User Pool** | Autenticación de usuarios | 3 |
| **S3 Bucket (archivos)** | Almacenar documentos subidos | 4 |
| **S3 Bucket + CloudFront (frontend)** | Hosting del SPA | 7 |
| **RDS PostgreSQL + pgvector** | Base de datos y vector store de producción | 7 |
| **EC2 (t3.xlarge sugerida)** | Backend FastAPI + Ollama | 7 |
| **Security Groups** | Reglas de red entre EC2 ↔ RDS | 7 |
| **Route 53 / DuckDNS** | Dominio para HTTPS | 7 |

---

## Documentación pendiente

- Scripts CLI para crear cada recurso
- Configuración de Nginx + Certbot (HTTPS Let's Encrypt)
- Pipeline de build/deploy del frontend a S3
- Variables de entorno de producción
