# Frontend — Agente RAG Gastronomía Colombiana

SPA construida con **React 18 + Vite + TypeScript + Tailwind + shadcn/ui**. Se conecta al backend FastAPI vía REST y a Cognito para autenticación.

> **Estado actual:** Fase 6.1 — esqueleto del proyecto.
> Las páginas son stubs visuales hasta las próximas fases.

---

## Stack

| Pieza | Tecnología |
|---|---|
| Bundler | Vite |
| Lenguaje | TypeScript (strict) |
| UI | React 18 |
| Estilos | Tailwind CSS 3 |
| Componentes | shadcn/ui (new-york style) |
| Routing | React Router v6 |
| HTTP | axios |
| Iconos | lucide-react |
| Notificaciones | sonner |
| Markdown | react-markdown |

---

## Requisitos

- **Node.js 20+** y **npm**

---

## Setup

```bash
cd frontend

# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# En M6.1 los valores por defecto funcionan;
# en M6.2 hay que rellenar las VITE_COGNITO_*

# 3. Levantar el dev server
npm run dev
```

Abre [http://localhost:5173](http://localhost:5173). Debes ver el header con navegación entre **Chat** y **Documentos**.

---

## Rutas disponibles (M6.1)

| Ruta | Descripción |
|---|---|
| `/` | Redirige a `/chat` |
| `/chat` | Stub de la página de chat (M6.4) |
| `/documents` | Stub de la página de documentos (M6.3) |
| `/login` | Stub del login (M6.2) |
| `/callback` | Stub del callback de Cognito (M6.2) |
| `*` | Redirige a `/chat` |

---

## Scripts

```bash
npm run dev          # Servidor de desarrollo con HMR
npm run build        # Build de producción → dist/
npm run preview      # Preview del build de producción
npm run type-check   # Solo type-check con tsc
```

---

## Estructura

```
frontend/
├── public/                       # Estáticos servidos como /
├── src/
│   ├── components/
│   │   ├── chat/                 # (M6.4) componentes del chat
│   │   ├── documents/            # (M6.3) componentes de documentos
│   │   ├── layout/               # Header, AppLayout
│   │   └── ui/                   # Componentes shadcn (button, ...)
│   ├── context/                  # (M6.2) AuthContext
│   ├── hooks/                    # (M6.2+) hooks personalizados
│   ├── lib/                      # utils (cn)
│   ├── pages/                    # Una por ruta
│   ├── services/                 # (M6.2+) api, auth, chat, documents
│   ├── types/                    # (M6.2+) tipos compartidos con el backend
│   ├── App.tsx                   # Routing
│   ├── main.tsx                  # Entry point (BrowserRouter, Toaster)
│   ├── index.css                 # Tailwind + variables shadcn
│   └── vite-env.d.ts             # Tipado de import.meta.env
├── index.html
├── package.json
├── vite.config.ts                # alias @/ → src/
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
├── components.json               # config shadcn
├── .env.example
├── .gitignore
└── README.md
```

---

## Próximas fases

| Fase | Implementa |
|---|---|
| M6.2 | Autenticación: AuthContext, login con Cognito Hosted UI, callback, PrivateRoute |
| M6.3 | Página de documentos: upload, list, delete, polling de status |
| M6.4 | Página de chat: sidebar de conversaciones, mensajes, sources, input |
| M6.5 | Pulido: loading states, manejo de errores, auto-scroll |

---

## Notas de desarrollo

**Alias `@/`**: importa desde `src/` con `@/`. Ej: `import { Button } from "@/components/ui/button"`.

**Agregar componentes shadcn nuevos**: la convención es copiarlos manualmente desde [ui.shadcn.com](https://ui.shadcn.com) al directorio `src/components/ui/`. En las próximas fases se irán agregando según se necesiten (input, dialog, skeleton, etc.).
