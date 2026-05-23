# Frontend — Agente RAG Gastronomía Colombiana

> **Estado actual:** Milestone 1 — aún no inicializado.
>
> El frontend se construirá en el **Milestone 6** con:
> - React 18 + Vite + TypeScript
> - Tailwind CSS + shadcn/ui
> - AWS Amplify Auth (Cognito)
> - axios con interceptor JWT

---

## Plan de inicialización (Milestone 6)

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npm install axios aws-amplify @aws-amplify/ui-react
npm install lucide-react
```

---

## Páginas previstas

| Ruta | Componente | Descripción |
|---|---|---|
| `/login` | `Login.tsx` | Inicio de sesión / registro con Cognito |
| `/chat` | `ChatPage.tsx` | Interfaz tipo chatbot con historial |
| `/documents` | `DocumentsPage.tsx` | Lista y carga de documentos |

---

## Despliegue (Milestone 7)

`npm run build` genera `dist/` que se sube a un bucket S3 + CloudFront.
