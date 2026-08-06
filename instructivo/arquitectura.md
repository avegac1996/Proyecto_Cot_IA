# Documento de Arquitectura — Sistema Inteligente de Cotización de Componentes Electrónicos

---

> **Estado del documento:** este archivo conserva la arquitectura objetivo y propuestas futuras. La arquitectura operativa y el despliegue vigente están documentados en [`../ARQUITECTURA.md`](../ARQUITECTURA.md). Redis, Celery y las colas programadas **no están implementados ni se despliegan actualmente**; el refresco de scraping vigente usa PostgreSQL y TTL por tienda bajo demanda.

## Tabla de Contenidos

1. [Visión del Proyecto](#1-visión-del-proyecto)
2. [Arquitectura General](#2-arquitectura-general)
3. [Módulos del Sistema](#3-módulos-del-sistema)
4. [Stack Tecnológico](#4-stack-tecnológico)
5. [Design System y Guía de Estilos](#5-design-system-y-guía-de-estilos)
6. [API REST — Endpoints](#6-api-rest--endpoints)
7. [Flujo Detallado de Cotización](#7-flujo-detallado-de-cotización)
8. [Modelo de Datos — Esquema de Tablas](#8-modelo-de-datos--esquema-de-tablas)
9. [Docker y Despliegue](#9-docker-y-despliegue)
10. [Buenas Prácticas](#10-buenas-prácticas)
11. [Estrategia de Testing](#11-estrategia-de-testing)
12. [Estructura del Repositorio](#12-estructura-del-repositorio)
13. [Próximos Pasos](#13-próximos-pasos)

---

## 1. Visión del Proyecto

### 1.1 Descripción General

Sistema web inteligente que automatiza la cotización de componentes electrónicos a partir de listas recibidas en múltiples formatos (audio, imagen, texto). El sistema procesa la información, identifica ambigüedades, consulta disponibilidad y precios en múltiples tiendas mediante web scraping, y genera cotizaciones formales con comparación de proveedores.

### 1.2 Problema que Resuelve

- **Proceso manual tedioso**: Las listas de componentes llegan en formatos variados y ambiguos, requiriendo trabajo manual intensivo.
- **Pérdida de ventas por demora**: Sin un sistema integrado, la lentitud en la cotización provoca pérdida de clientes.
- **Falta de normalización**: Los clientes usan términos coloquiales o ambiguos (ej. "el foquito ese chiquito" → LED RGB 5mm).
- **Sin histórico de cotizaciones**: No existe un repositorio de cotizaciones previas para evitar búsquedas repetidas.

### 1.3 Usuarios Objetivo

El sistema maneja dos roles de usuario:

| Rol | Descripción | Permisos |
|---|---|---|
| **admin** | Administrador de la tienda | Crear usuarios, desactivar usuarios, gestionar tiendas, gestionar banco de preguntas, ver historial completo, cotizar |
| **user** | Vendedor / operador | Cotizar, ver su historial, cargar archivos, responder preguntas |

**Usuarios por defecto** (se crean automáticamente al inicializar la BD):

| Usuario | Email | Rol | Contraseña |
|---|---|---|---|
| `admin` | admin@cotia.com | admin | Admin123! |
| `user` | user@cotia.com | user | User123! |

> **Nota de seguridad**: Las contraseñas por defecto deben cambiarse en el primer inicio de sesión. El admin puede cambiarlas desde el módulo de gestión de usuarios.

### 1.4 Objetivos Funcionales

| ID    | Objetivo                   | Descripción                                                              |
| -------| ----------------------------| --------------------------------------------------------------------------|
| OF-1  | Ingesta multimodal         | Recibir listas en audio, imagen o texto y extraer componentes            |
| OF-2  | Normalización inteligente  | Traducir términos coloquiales/ambiguos a productos estandarizados        |
| OF-3  | Resolución de ambigüedades | Hacer preguntas inteligentes al usuario para completar datos faltantes   |
| OF-4  | Búsqueda multi-tienda      | Consultar disponibilidad y precios en múltiples tiendas vía web scraping |
| OF-5  | Comparación de precios     | Mostrar precios de cada proveedor con margen del 5% sobre competencia    |
| OF-6  | Generación de cotización   | Producir cotización formal descargable en PDF y Excel                    |
| OF-7  | Histórico de cotizaciones  | Guardar cotizaciones previas para evitar scraping repetido               |
| OF-8  | Interfaz responsive        | Funcionar correctamente en móvil y escritorio                            |
| OF-9  | Autenticación de usuarios  | Login con JWT, dos roles (admin y user), usuarios por defecto            |
| OF-10 | Gestión de usuarios        | Admin crea usuarios y los desactiva (no elimina)                         |

### 1.5 Objetivos No Funcionales

| ID    | Objetivo       | Descripción                                    |
| -------| ----------------| ------------------------------------------------|
| ONF-1 | Rendimiento    | Respuesta de API < 500ms (excluyendo scraping) |
| ONF-2 | Disponibilidad | 99.5% uptime                                   |
| ONF-3 | Escalabilidad  | Soportar 50 usuarios concurrentes              |
| ONF-4 | Seguridad      | HTTPS, validación de inputs, CORS estricto     |
| ONF-5 | Mantenibilidad | Código documentado, testado, con CI/CD         |
| ONF-6 | Portabilidad   | Despliegue con Docker en cualquier entorno     |

---

## 2. Arquitectura General

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Navegador Web)                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐     │
│  │ Carga de  │  │ Diálogo   │  │ Visualizar│  │ Descargar     │     │
│  │ Archivos  │  │ Preguntas │  │ Cotización │  │ Cotización    │     │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘     │
└────────┼─────────────┼───────────────┼───────────────┼──────────────┘
         │             │               │               │
         └─────────────┴───────┬───────┴───────────────┘
                               │  HTTP/HTTPS (REST API)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              FRONTEND (React + Vite — Arquitectura Modular)          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Módulo Login (pantalla inicial)                 │   │
│  │  Email + Contraseña → JWT → Redirect a App Shell              │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │ (autenticado)                      │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │                    Módulo Header                              │   │
│  │  Logo | Tabs | Toggle tema | Usuario (rol) | Logout         │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │              Contenido (cambia por pestaña)                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │ Módulo   │ │ Módulo   │ │ Módulo   │ │ Módulo         │  │   │
│  │  │ Carga    │ │ Preguntas│ │ Cotiza- │ │ Historial      │  │   │
│  │  │ Archivos │ │ (Chat)   │ │ ción    │ │ Cotizaciones   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │
│  │  ┌────────────────┐                                        │   │
│  │  │ Módulo Usuarios │ (solo admin)                            │   │
│  │  └────────────────┘                                        │   │
│  └─────────────────────────────┬───────────────────────────────┘   │
│                                │                                    │
│  ┌─────────────────────────────▼───────────────────────────────┐   │
│  │                    Módulo Footer                              │   │
│  │  Info del proyecto | Links | Versión | Copyright              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Router   │ │ Store    │ │ API      │ │ UI       │ │ Design   │ │
│  │ (React   │ │ (Zustand)│ │ Client   │ │ Base     │ │ System   │ │
│  │  Router) │ │          │ │ (Axios)  │ │ (shadcn) │ │ (CSS)    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │  REST API (JSON)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Orquestador de Procesos                   │   │
│  └─────────┬───────────┬──────────────┬─────────────┬──────────┘   │
│            │           │              │             │               │
│  ┌─────────▼───┐ ┌─────▼─────┐ ┌──────▼──────┐ ┌───▼──────────┐    │
│  │ Motor de    │ │ Motor de  │ │ Sistema de  │ │ Generador de │    │
│  │ Ingesta     │ │ Matching  │ │ Preguntas   │ │ Cotizaciones │    │
│  │ Multimodal  │ │ Inteligente│ │ Inteligentes│ │              │    │
│  └─────────┬───┘ └─────┬─────┘ └──────┬──────┘ └───┬──────────┘    │
│            │           │              │             │               │
│  ┌─────────▼───┐ ┌─────▼─────┐       │        ┌───▼──────────┐    │
│  │ OCR / STT / │ │ Diccionario│       │        │ Comparador   │    │
│  │ NLP         │ │ Equivalenc│       │        │ de Precios   │    │
│  └─────────────┘ └───────────┘       │        └───┬──────────┘    │
│                                     │             │               │
│  ┌──────────────────────────────────▼─────────────▼──────────┐    │
│  │                   Web Scraping Engine                     │    │
│  │  ┌──────────┐  ┌───────────┐  ┌────────────┐              │    │
│  │  │ AV       │  │ Megatronica│  │ Electro    │              │    │
│  │  │Electronics│  │           │  │ Store      │              │    │
│  │  └──────────┘  └───────────┘  └────────────┘              │    │
│  └──────────────────────────┬────────────────────────────────┘    │
│                             │                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              Base de Datos (PostgreSQL)                       │    │
│  │  Usuarios | Productos | Cotizaciones | Sesiones              │    │
│  │  Cache Scraping | Equivalencias | Banco Preguntas | Tiendas   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Redis (Cache + Cola de tareas Celery)           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Diagrama de Despliegue con Docker

```
┌─────────────────────────────────────────────┐
│              Docker Compose                 │
│                                             │
│  ┌──────────────┐    ┌──────────────────┐   │
│  │  frontend     │    │   backend        │   │
│  │  (Vite/Nginx) │    │   (FastAPI/      │   │
│  │  :5173        │    │   Uvicorn)       │   │
│  │               │◄──►│   :8000          │   │
│  └──────────────┘    └────────┬─────────┘   │
│                              │              │
│              ┌───────────────┼──────────┐   │
│              │               │          │   │
│  ┌───────────▼──┐   ┌───────▼────────┐ │   │
│  │  postgres     │   │  redis          │ │   │
│  │  :5432        │   │  :6379          │ │   │
│  └───────┬───────┘   └────────────────┘ │   │
│          │                              │   │
│  ┌───────▼────────┐                     │   │
│  │  pgadmin        │   ┌──────────────┐ │   │
│  │  :5050          │   │ celery-worker │ │   │
│  └────────────────┘   │ (scraping)    │ │   │
│                       └──────────────┘ │   │
└─────────────────────────────────────────────┘
```

### 2.3 Flujo de Alto Nivel

```
Cliente envía lista (audio/imagen/texto)
        │
        ▼
Motor de Ingesta Multimodal → Extrae texto plano con lista de componentes
        │
        ▼
Motor de Matching Inteligente → Normaliza términos ambiguos a productos estandarizados
        │
        ▼
Sistema de Preguntas Inteligentes → Detecta ambigüedades y consulta al usuario
        │
        ▼
Web Scraping Engine → Busca disponibilidad y precios en tiendas
        │
        ▼
Comparador de Precios → Aplica margen del 5% sobre productos de competencia
        │
        ▼
Generador de Cotizaciones → Formatea cotización final con desglose por proveedor
        │
        ▼
Cliente recibe cotización + descarga en formato PDF/Excel
```

---

## 3. Módulos del Sistema

### 3.1 Frontend (Aplicación Web Modular con React)

**Responsabilidad**: Interfaz de usuario modular organizada por pestañas, con módulos independientes para cada funcionalidad y módulos de layout (header/footer) reutilizables.

**Principios de diseño**:
- **Arquitectura modular**: Cada funcionalidad es un módulo independiente con sus propios componentes, hooks, servicios y estilos.
- **Navegación por pestañas**: El usuario navega entre módulos mediante tabs en el header, sin recargas de página.
- **Módulos de layout**: Header y Footer son módulos separados que se renderizan en todas las vistas.
- **React liviano**: Sin dependencias pesadas, solo lo necesario para una SPA rápida.
- **Lazy loading**: Cada módulo se carga bajo demanda para mantener el bundle inicial pequeño.

**Características clave**:
- Carga de archivos (audio, imagen, texto) con drag & drop
- Chat interactivo para responder preguntas de aclaración
- Visualización de cotización con desglose por proveedor y precios
- Descarga de cotización en PDF/Excel
- Diseño responsive optimizado para móvil
- Soporte para modo oscuro/claro
- Notificaciones en tiempo real (toast notifications)

**Módulos de la aplicación**:

| Módulo | Pestaña | Descripción |
|---|---|---|
| **Header** | (global) | Logo, tabs de navegación, toggle tema claro/oscuro, info de usuario (rol + logout) |
| **Footer** | (global) | Info del proyecto, links, versión, copyright |
| **Login** | (auth) | Pantalla de login con email + contraseña, no requiere tabs |
| **Carga** | Tab 1 | Carga de archivos (audio, imagen, texto) con drag & drop |
| **Preguntas** | Tab 2 | Chat interactivo para resolver ambigüedades |
| **Cotización** | Tab 3 | Tabla de cotización con selección de proveedores, descarga PDF/Excel |
| **Historial** | Tab 4 | Listado de cotizaciones previas con búsqueda |
| **Gestión Usuarios** | Tab 5 (solo admin) | Listar usuarios, crear usuarios, desactivar/activar usuarios |

**Diagrama de módulos**:

```
┌─────────────────────────────────────────────────────────┐
│              Módulo Login (pantalla inicial)             │
│  Email + Contraseña → JWT → Redirect a App Shell         │
└─────────────────────────────────────────────────────────┘
                          │ (autenticado)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    APP SHELL (Layout)                    │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Módulo Header                         │  │
│  │  [Logo] [Tab: Carga] [Tab: Preguntas]              │  │
│  │  [Tab: Cotización] [Tab: Historial] [🌙 Tema]     │  │
│  │  [Tab: Usuarios (solo admin)] [👤 user@cotia.com]  │  │
│  │  [Cerrar sesión]                                   │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                              │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │         Contenido (renderiza módulo activo)       │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Módulo Carga (Tab 1)                        │ │  │
│  │  │  ├── DropZone.tsx                           │ │  │
│  │  │  ├── FilePreview.tsx                        │ │  │
│  │  │  ├── UploadButton.tsx                       │ │  │
│  │  │  ├── useUpload.ts (hook)                    │ │  │
│  │  │  └── uploadService.ts (API)                 │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Módulo Preguntas (Tab 2)                  │ │  │
│  │  │  ├── ChatContainer.tsx                     │ │  │
│  │  │  ├── MessageBubble.tsx                     │ │  │
│  │  │  ├── QuestionCard.tsx                      │ │  │
│  │  │  ├── useChat.ts (hook)                     │ │  │
│  │  │  └── preguntasService.ts (API)             │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Módulo Cotización (Tab 3)                │ │  │
│  │  │  ├── CotizacionTable.tsx                   │ │  │
│  │  │  ├── ProveedorCard.tsx                     │ │  │
│  │  │  ├── DownloadButtons.tsx                   │ │  │
│  │  │  ├── useCotizacion.ts (hook)              │ │  │
│  │  │  └── cotizacionService.ts (API)           │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Módulo Historial (Tab 4)                 │ │  │
│  │  │  ├── HistorialList.tsx                     │ │  │
│  │  │  ├── HistorialCard.tsx                     │ │  │
│  │  │  ├── SearchBar.tsx                         │ │  │
│  │  │  ├── useHistorial.ts (hook)                │ │  │
│  │  │  └── historialService.ts (API)            │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │  ┌─────────────────────────────────────────────┐ │  │
│  │  │  Módulo Gestión Usuarios (Tab 5 - admin)  │ │  │
│  │  │  ├── UserList.tsx                          │ │  │
│  │  │  ├── UserCreateForm.tsx                    │ │  │
│  │  │  ├── UserToggleActive.tsx                  │ │  │
│  │  │  ├── useUsuarios.ts (hook)                 │ │  │
│  │  │  └── usuariosService.ts (API)             │ │  │
│  │  └─────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Módulo Footer                         │  │
│  │  [Info proyecto] [Links] [v1.0.0] [© 2026]       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Stack**:
- **Framework**: React 18 + Vite (bundle liviano)
- **Estilos**: TailwindCSS + Design System propio (ver sección 5)
- **Componentes UI base**: shadcn/ui + Lucide icons
- **HTTP Client**: Axios con interceptores
- **Gestión de estado**: Zustand (liviano, sin boilerplate)
- **Routing**: React Router v6 (lazy loading por módulo)
- **Validación de formularios**: React Hook Form + Zod
- **Notificaciones**: Sonner (toast)

**Estructura de carpetas (modular)**:
```
FRONTEND/
├── public/
│   ├── design-system.html       # Guía visual de estilos (HTML)
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── app/                    # App shell y layout global
│   │   ├── App.tsx              # Root component
│   │   ├── AppShell.tsx         # Layout con Header + Content + Footer
│   │   ├── AppRouter.tsx        # Router con lazy loading por módulo
│   │   └── AppProviders.tsx     # Providers (theme, toast, etc.)
│   │
│   ├── modules/                # Módulos de la aplicación
│   │   ├── login/              # Módulo Login (pantalla inicial, sin tabs)
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── LoginError.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useLogin.ts
│   │   │   ├── services/
│   │   │   │   └── authService.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── LoginPage.tsx
│   │   │
│   │   ├── header/             # Módulo Header (global)
│   │   │   ├── Header.tsx
│   │   │   ├── HeaderTabs.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   ├── UserMenu.tsx
│   │   │   └── header.module.css
│   │   │
│   │   ├── footer/             # Módulo Footer (global)
│   │   │   ├── Footer.tsx
│   │   │   ├── FooterLinks.tsx
│   │   │   └── footer.module.css
│   │   │
│   │   ├── carga/              # Módulo Carga de Archivos (Tab 1)
│   │   │   ├── components/
│   │   │   │   ├── DropZone.tsx
│   │   │   │   ├── FilePreview.tsx
│   │   │   │   └── UploadButton.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useUpload.ts
│   │   │   ├── services/
│   │   │   │   └── uploadService.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── CargaPage.tsx    # Página del módulo
│   │   │
│   │   ├── preguntas/          # Módulo Preguntas (Tab 2)
│   │   │   ├── components/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   └── QuestionCard.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useChat.ts
│   │   │   ├── services/
│   │   │   │   └── preguntasService.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── PreguntasPage.tsx
│   │   │
│   │   ├── cotizacion/        # Módulo Cotización (Tab 3)
│   │   │   ├── components/
│   │   │   │   ├── CotizacionTable.tsx
│   │   │   │   ├── ProveedorCard.tsx
│   │   │   │   ├── ItemRow.tsx
│   │   │   │   └── DownloadButtons.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useCotizacion.ts
│   │   │   ├── services/
│   │   │   │   └── cotizacionService.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── CotizacionPage.tsx
│   │   │
│   │   ├── historial/        # Módulo Historial (Tab 4)
│   │   │   ├── components/
│   │   │   │   ├── HistorialList.tsx
│   │   │   │   ├── HistorialCard.tsx
│   │   │   │   └── SearchBar.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useHistorial.ts
│   │   │   ├── services/
│   │   │   │   └── historialService.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   └── HistorialPage.tsx
│   │   │
│   │   └── usuarios/          # Módulo Gestión de Usuarios (Tab 5 - solo admin)
│   │       ├── components/
│   │       │   ├── UserList.tsx
│   │       │   ├── UserCreateForm.tsx
│   │       │   └── UserToggleActive.tsx
│   │       ├── hooks/
│   │       │   └── useUsuarios.ts
│   │       ├── services/
│   │       │   └── usuariosService.ts
│   │       ├── types/
│   │       │   └── index.ts
│   │       └── UsuariosPage.tsx
│   │
│   ├── shared/                # Recursos compartidos entre módulos
│   │   ├── components/         # Componentes UI base (shadcn/ui)
│   │   │   ├── ui/             # Button, Input, Card, Badge, etc.
│   │   │   └── common/         # Loading, ErrorBoundary, EmptyState
│   │   ├── lib/
│   │   │   ├── api.ts          # Cliente Axios configurado
│   │   │   ├── utils.ts        # Utilidades (cn, formatCurrency, etc.)
│   │   │   └── constants.ts   # Constantes de la app
│   │   ├── store/
│   │   │   ├── authStore.ts       # Auth state (JWT, user, login/logout)
│   │   │   ├── cotizacionStore.ts  # Estado global (Zustand)
│   │   │   └── uiStore.ts        # Tema, tab activa, etc.
│   │   ├── types/
│   │   │   └── index.ts        # Tipos TypeScript compartidos
│   │   └── hooks/
│   │       └── useTheme.ts    # Hook de tema claro/oscuro
│   │
│   ├── styles/
│   │   └── globals.css        # Tailwind + variables CSS del design system
│   │
   └── main.tsx               # Entry point
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── Dockerfile
├── index.html
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── vite.config.ts
```

### 3.2 Backend (API Gateway + Orquestador)

**Responsabilidad**: Recibir peticiones del frontend, orquestar los módulos del sistema y devolver respuestas.

**Características clave**:
- API REST para endpoints de cotización
- Endpoints para carga de archivos (multipart/form-data)
- Endpoints para diálogo de preguntas/respuestas
- Gestión de sesiones de cotización
- Manejo de errores centralizado con códigos estándar
- Logging estructurado
- Rate limiting por IP
- Documentación automática con OpenAPI/Swagger

**Stack**:
- **Framework**: FastAPI (Python 3.14+)
- **Servidor**: Uvicorn (ASGI)
- **Validación**: Pydantic v2
- **ORM**: SQLAlchemy 2.0 (async)
- **Migraciones**: Alembic
- **Autenticación**: JWT (python-jose) — obligatorio, dos roles (admin y user)
- **Hash de passwords**: bcrypt (passlib)
- **Logging**: structlog o loguru
- **Testing**: pytest + pytest-asyncio + httpx

**Estructura de carpetas**:
```
BACKEND/
├── app/
│   ├── main.py                  # Entry point FastAPI
│   ├── core/
│   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   ├── database.py          # Conexión SQLAlchemy async
│   │   ├── security.py          # JWT, CORS, rate limiting
│   │   └── logging.py           # Configuración de logging
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependencias inyectables (auth, DB session)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # Router principal
│   │       └── endpoints/
│   │           ├── auth.py       # Login, me, refresh
│   │           ├── usuarios.py   # CRUD usuarios (solo admin)
│   │           ├── upload.py     # Carga de archivos
│   │           ├── cotizacion.py # Cotizaciones
│   │           ├── preguntas.py  # Preguntas/respuestas
│   │           ├── productos.py  # Búsqueda de productos
│   │           └── health.py    # Health check
│   ├── models/
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── producto.py
│   │   ├── cotizacion.py
│   │   ├── equivalencia.py
│   │   ├── scraping_cache.py
│   │   ├── banco_preguntas.py
│   │   └── tienda.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # LoginRequest, TokenResponse, UserResponse
│   │   ├── usuario.py          # UsuarioCreate, UsuarioUpdate, UsuarioResponse
│   │   ├── producto.py
│   │   ├── cotizacion.py
│   │   ├── upload.py
│   │   └── preguntas.py
│   ├── services/
│   │   ├── ingesta/
│   │   │   ├── __init__.py
│   │   │   ├── audio.py         # Speech-to-Text
│   │   │   ├── imagen.py        # OCR
│   │   │   ├── texto.py         # Parseo de texto
│   │   │   └── nlp.py           # Extracción de entidades
│   │   ├── matching/
│   │   │   ├── __init__.py
│   │   │   ├── normalizer.py    # Normalización de términos
│   │   │   ├── equivalences.py  # Diccionario de equivalencias
│   │   │   └── semantic.py      # Matching semántico con LLM
│   │   ├── preguntas/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py      # Detección de ambigüedades
│   │   │   └── selector.py     # Selección de preguntas
│   │   ├── scraping/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Scraper abstracto
│   │   │   ├── av_electronics.py
│   │   │   ├── megatronica.py
│   │   │   ├── electro_store.py
│   │   │   └── cache.py        # Gestión de cache
│   │   └── cotizacion/
│   │       ├── __init__.py
│   │       ├── comparator.py    # Comparación de precios
│   │       ├── generator.py     # Generación de cotización
│   │       └── exporter.py      # PDF/Excel
│   └── utils/
│       ├── __init__.py
│       ├── files.py            # Manejo de archivos
│       └── validators.py       # Validadores auxiliares
├── alembic/
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_usuarios.py
│   ├── test_upload.py
│   ├── test_cotizacion.py
│   ├── test_matching.py
│   ├── test_scraping.py
│   └── test_preguntas.py
├── .env.example
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

### 3.3 Motor de Ingesta Multimodal

**Responsabilidad**: Procesar archivos de entrada (audio, imagen, texto) y extraer la lista de componentes electrónicos en texto plano.

**Submódulos**:

| Tipo de Entrada | Tecnología | Función |
|---|---|---|
| **Audio** | Speech-to-Text (OpenAI Whisper API) | Transcribir audio a texto |
| **Imagen** | OCR (Tesseract / Google Vision API) | Extraer texto de imágenes/fotos |
| **Texto** | Parser directo (Python) | Leer archivos .txt, .csv, .docx |
| **NLP** | spaCy + LLM API (OpenAI/Gemini) | Identificar entidades (componentes, cantidades, especificaciones) |

**Formatos aceptados**:

| Tipo | Extensiones | Tamaño máximo |
|---|---|---|
| Audio | .mp3, .wav, .m4a, .ogg | 25 MB |
| Imagen | .jpg, .jpeg, .png, .webp | 10 MB |
| Texto | .txt, .csv, .docx, .pdf | 5 MB |

**Flujo interno**:
```
Archivo de entrada → Validación de tipo/tamaño → Conversión a texto plano → NLP Entity Extraction → Lista estructurada de componentes
```

**Salida esperada**: Lista estructurada en formato JSON:
```json
{
  "componentes": [
    {
      "tipo": "resistencia",
      "valor": "220",
      "unidad": "ohm",
      "potencia": null,
      "cantidad": 5,
      "ambiguo": false
    },
    {
      "tipo": "led",
      "color": null,
      "tamano": null,
      "cantidad": 10,
      "ambiguo": true,
      "ambiguedades": ["color", "tamano"]
    }
  ]
}
```

### 3.4 Motor de Matching Inteligente

**Responsabilidad**: Normalizar términos ambiguos o coloquiales a productos estandarizados del catálogo.

**Características clave**:
- **Diccionario de equivalencias**: Mapeo de términos coloquiales a términos técnicos
  - Ej: "foquito ese chiquito" → LED, "tablita blanca de huequitos" → Protoboard
- **Diccionario de sinónimos**: Múltiples formas de referirse al mismo componente
  - Ej: "Arduino" = "placa Arduino UNO" = "tarjeta de desarrollo Arduino"
- **Matching de especificaciones**: Identificar valores numéricos y unidades
  - Ej: "resistencia de 220" → 220 Ω, "capacitor de 220uf" → 220 µF
- **Detección de equivalencias técnicas**: Componentes funcionalmente compatibles
  - Ej: LM35 ↔ DS18B20 (sensores de temperatura), 2N3904 ↔ BC547 (transistores NPN)

**Tecnologías**:
- **Diccionario de equivalencias**: Tabla en PostgreSQL + embeddings semánticos
- **Matching semántico**: Sentence-transformers o LLM API (OpenAI/Gemini)
- **Normalización de unidades**: Regex + tabla de conversión

### 3.5 Sistema de Preguntas Inteligentes

**Responsabilidad**: Detectar ambigüedades en la lista de componentes y generar preguntas de aclaración al usuario.

**Estructura del banco de preguntas** (basado en `preguntas.txt`):

| Categoría | Nº de Preguntas | Ejemplo |
|---|---|---|
| Información general | 5 | "¿Podría confirmar si la lista enviada está completa?" |
| Cantidades | 4 | "¿Podría confirmar la cantidad exacta de unidades?" |
| Resistencias | 3 | "¿Cuál es el valor de la resistencia? (220 Ω, 1 kΩ, 10 kΩ)" |
| Capacitores | 3 | "¿Podría indicar la capacitancia del capacitor?" |
| LED | 3 | "¿Qué color o colores de LED necesita?" |
| Transistores | 2 | "¿El transistor es NPN, PNP, MOSFET u otro tipo?" |
| Diodos | 2 | "¿Necesita un diodo rectificador, Zener, Schottky?" |
| Circuitos integrados | 2 | "¿Necesita encapsulado DIP, SMD u otro formato?" |
| Sensores y módulos | 2 | "¿Podría indicar la aplicación o función del sensor?" |
| Fuentes de alimentación | 1 | "¿Qué voltaje y corriente necesita?" |
| Conectores y cables | 2 | "¿Qué tipo de conector requiere?" |
| Confirmación final | 1 | "¿Desea realizar alguna modificación adicional?" |

**Lógica de selección de preguntas**:
1. Tras el matching inteligente, identificar campos faltantes o ambiguos por componente.
2. Seleccionar preguntas del banco según la categoría del componente y los campos faltantes.
3. Priorizar preguntas que desambigüen múltiples componentes a la vez (ej. colores de LEDs).
4. Limitar el número de preguntas por sesión para no saturar al usuario (máximo 5 preguntas por sesión).

**Integración con conocimiento de tienda** (basado en `preguntas_10_GD.pdf` y `preguntas_clientes_electronica.pdf`):
- Las respuestas de la tienda sobre compatibilidad, equivalentes y recomendaciones se usan como contexto para enriquecer las preguntas y sugerir alternativas.

### 3.6 Web Scraping Engine

**Responsabilidad**: Buscar disponibilidad y precios de componentes en las tiendas de la competencia.

**Tiendas objetivo**:

| Tienda | URL | Estado |
|---|---|---|
| AV Electronics | `https://avelectronics.cc/` | Pendiente de análisis |
| Megatronica | `https://megatronica.cc/` | Pendiente de análisis |
| Electro Store | `https://electrostoree.com/` | Pendiente de análisis |

**Arquitectura del scraper**:

```
┌─────────────────────────────────────────────┐
│            Web Scraping Engine              │
│                                             │
│  ┌─────────────┐  ┌────────────────────┐   │
│  │ Scraper     │  │ Cache Manager      │   │
│  │ Interface   │  │ (verifica DB antes │   │
│  │ (abstract)  │  │  de hacer scraping)│   │
│  └──────┬──────┘  └────────────────────┘   │
│         │                                   │
│  ┌──────▼──────────────────────────────┐   │
│  │        Scrappers por Tienda          │   │
│  │  ┌────────────┐ ┌────────────────┐  │   │
│  │  │ AV          │ │ Megatronica    │  │   │
│  │  │ Electronics │ │ Scraper       │  │   │
│  │  │ Scraper    │ │                │  │   │
│  │  └────────────┘ └────────────────┘  │   │
│  │  ┌──────────────────────────────┐  │   │
│  │  │ Electro Store Scraper       │  │   │
│  │  └──────────────────────────────┘  │   │
│  └────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

**Consideraciones técnicas**:
- **Rate limiting**: Máximo 1 petición por segundo por tienda.
- **robots.txt**: Verificar y respetar las políticas de cada sitio.
- **Cache en BD**: Antes de hacer scraping, verificar si el producto ya fue consultado recientemente (TTL configurable, ej. 24 horas).
- **Manejo de cambios**: Los sitios web pueden cambiar su estructura; usar selectores CSS/XPath configurables en la tabla `tiendas`.
- **Manejo de errores**: Timeout (30s), producto no encontrado, precio no disponible.
- **User-Agent**: Usar User-Agent legítimo y identificable.
- **Fallback**: Si un scraper falla, continuar con las demás tiendas.

**Tecnologías**:
- **Librería estática**: BeautifulSoup4 + requests
- **Librería dinámica (JS)**: Playwright (para sitios que requieren renderizado)
- **Scheduler**: Celery + Redis (para scraping programado de catálogos completos)
- **Estrategia**: Scraping bajo demanda (por producto) + scraping programado (catálogo completo nocturno)

### 3.7 Base de Datos (PostgreSQL con Docker)

**Responsabilidad**: Almacenar productos, cotizaciones, cache de scraping y diccionarios de equivalencias.

**Tecnologías**:
- **Motor**: PostgreSQL 16 (contenedor Docker)
- **ORM**: SQLAlchemy 2.0 (async) con asyncpg
- **Migraciones**: Alembic
- **Pool de conexiones**: SQLAlchemy pool con asyncpg

**Modelo de datos**: Ver sección 8.

### 3.8 Cache y Cola de Tareas (Redis)

**Responsabilidad**: Cache de respuestas frecuentes y cola de tareas para scraping programado.

**Usos**:
- **Cache de sesión**: Almacenar el estado de la cotización en progreso.
- **Cache de respuestas de LLM**: Evitar llamadas repetidas a APIs de IA.
- **Cola Celery**: Tareas de scraping programado de catálogos completos.
- **Rate limiting**: Contador de peticiones por IP.

**Tecnologías**:
- **Redis 7** (contenedor Docker)
- **Celery** con Redis como broker

### 3.9 Generador de Cotizaciones

**Responsabilidad**: Comparar precios entre proveedores, aplicar márgenes y generar la cotización final.

**Lógica de negocio**:
1. **Inventario propio**: Si el producto está en stock de la tienda principal, usar precio directo.
2. **Competencia**: Si el producto se obtiene de tiendas competidoras, aplicar **margen del 5%** sobre el precio.
3. **Comparación**: Mostrar todos los proveedores con precio y disponibilidad.
4. **Decisión del usuario**: El usuario decide qué productos cotizar y de qué proveedor.
5. **Formato de salida**: Cotización formal con desglose por ítem, proveedor, precio unitario, subtotal y total.

**Formato de salida**:
- Visualización en la web (tabla responsive)
- Descarga en PDF (WeasyPrint)
- Descarga en Excel/CSV (openpyxl)

**Tecnologías**:
- **PDF**: WeasyPrint (Python) — soporta HTML/CSS para diseño profesional
- **Excel**: openpyxl (Python)

---

## 4. Stack Tecnológico

### 4.1 Tabla Resumida

| Capa | Tecnología | Versión | Justificación |
|---|---|---|---|
| **Frontend** | React + Vite | React 18, Vite 5 | Responsive, ecosistema maduro, ideal para SPA |
| **Estilos Frontend** | TailwindCSS | 3.4+ | Utility-first, diseño consistente, modo oscuro |
| **Componentes UI** | shadcn/ui + Lucide | Última | Componentes accesibles y personalizables |
| **Estado Frontend** | Zustand | 4.5+ | Simple, sin boilerplate, performante |
| **Backend** | FastAPI (Python) | 0.110+ | Rápido, async nativo, documentación automática |
| **Runtime Python** | Python | 3.14+ | Performance, match statements, type hints |
| **Base de Datos** | PostgreSQL | 16 | Robusto, JSONB, full-text search |
| **ORM** | SQLAlchemy + Alembic | 2.0+ | Estándar de facto, async, migraciones |
| **Autenticación** | python-jose (JWT) + passlib (bcrypt) | — | JWT tokens, hash de passwords seguro |
| **Cache/Cola** | Redis | 7+ | Cache de sesión, Celery broker |
| **Web Scraping** | BeautifulSoup4 + Playwright | 4.12+ / 1.40+ | Estático + dinámico (JS) |
| **OCR** | Tesseract / Google Vision API | — | Extracción de texto desde imágenes |
| **Speech-to-Text** | OpenAI Whisper API | — | Transcripción de audio a texto |
| **NLP / Matching** | spaCy + LLM API (OpenAI/Gemini) | 3.7+ | Extracción de entidades + matching semántico |
| **Generación PDF** | WeasyPrint | 60+ | HTML/CSS → PDF, diseño profesional |
| **Generación Excel** | openpyxl | 3.1+ | Cotizaciones en Excel/CSV |
| **Contenedores** | Docker + Docker Compose | 24+ | Portabilidad, aislamiento, reproducibilidad |
| **Testing Backend** | pytest + httpx | 8+ | Tests unitarios, integración, async |
| **Testing Frontend** | Vitest + Testing Library | 1+ | Tests unitarios y de componentes |
| **Linting** | ESLint + Prettier (Front), Ruff (Back) | — | Calidad y consistencia de código |
| **CI/CD** | GitHub Actions | — | Automatización de tests y despliegue |

### 4.2 Diagrama de Versiones y Compatibilidad

```
Python 3.14+ ──┬── FastAPI 0.110+
               ├── SQLAlchemy 2.0+ (async)
               ├── asyncpg
               ├── Pydantic 2.0+
               ├── python-jose (JWT)
               ├── passlib + bcrypt
               ├── BeautifulSoup4
               ├── Playwright
               ├── WeasyPrint
               ├── openpyxl
               ├── Celery
               └── Redis (redis-py)

Node 24+ ─────┬── React 18
              ├── Vite 5
              ├── TailwindCSS 3.4+
              ├── shadcn/ui
              ├── Zustand 4.5+
              ├── React Router 6
              ├── Axios
              └── Vitest

Docker 24+ ───┬── PostgreSQL 16
              ├── Redis 7
              ├── Backend (Python)
              └── Frontend (Nginx)
```

---

## 5. Design System y Guía de Estilos

### 5.1 Propósito

El Design System define la identidad visual del proyecto: colores, tipografía, espaciado, bordes, sombras y componentes. Se mantiene una guía de estilos en un archivo HTML independiente que sirve como referencia visual para el equipo de desarrollo.

### 5.2 Paleta de Colores

#### Colores Primarios (Marca)

| Token | Hex | Uso |
|---|---|---|
| `--color-primary` | `#0F4C75` | Azul principal — botones, links, headers |
| `--color-primary-dark` | `#0A3450` | Hover states, elementos activos |
| `--color-primary-light` | `#3282B8` | Elementos secundarios, badges |
| `--color-primary-lighter` | `#BBE1FA` | Fondos suaves, hover claro |

#### Colores de Estado

| Token | Hex | Uso |
|---|---|---|
| `--color-success` | `#16A34A` | Disponible, cotización completada |
| `--color-success-light` | `#DCFCE7` | Fondo de success |
| `--color-warning` | `#F59E0B` | Stock bajo, ambigüedad detectada |
| `--color-warning-light` | `#FEF3C7` | Fondo de warning |
| `--color-error` | `#DC2626` | No disponible, error |
| `--color-error-light` | `#FEE2E2` | Fondo de error |
| `--color-info` | `#0EA5E9` | Información, tooltips |
| `--color-info-light` | `#E0F2FE` | Fondo de info |

#### Colores Neutros (Modo Claro)

| Token | Hex | Uso |
|---|---|---|
| `--color-bg` | `#FFFFFF` | Fondo principal |
| `--color-bg-secondary` | `#F8FAFC` | Fondo de cards, sidebar |
| `--color-bg-tertiary` | `#F1F5F9` | Fondo de inputs, hover |
| `--color-border` | `#E2E8F0` | Bordes, divisores |
| `--color-text` | `#0F172A` | Texto principal |
| `--color-text-secondary` | `#475569` | Texto secundario |
| `--color-text-muted` | `#94A3B8` | Texto deshabilitado, placeholders |

#### Colores Neutros (Modo Oscuro)

| Token | Hex | Uso |
|---|---|---|
| `--color-bg` | `#0F172A` | Fondo principal |
| `--color-bg-secondary` | `#1E293B` | Fondo de cards, sidebar |
| `--color-bg-tertiary` | `#334155` | Fondo de inputs, hover |
| `--color-border` | `#475569` | Bordes, divisores |
| `--color-text` | `#F1F5F9` | Texto principal |
| `--color-text-secondary` | `#CBD5E1` | Texto secundario |
| `--color-text-muted` | `#64748B` | Texto deshabilitado, placeholders |

### 5.3 Tipografía

| Elemento | Fuente | Tamaño | Peso | Line-height |
|---|---|---|---|---|
| H1 | Inter | 2.25rem (36px) | 700 | 1.2 |
| H2 | Inter | 1.875rem (30px) | 700 | 1.25 |
| H3 | Inter | 1.5rem (24px) | 600 | 1.3 |
| H4 | Inter | 1.25rem (20px) | 600 | 1.35 |
| Body | Inter | 1rem (16px) | 400 | 1.5 |
| Body Small | Inter | 0.875rem (14px) | 400 | 1.5 |
| Caption | Inter | 0.75rem (12px) | 400 | 1.4 |
| Button | Inter | 0.875rem (14px) | 600 | 1.4 |
| Label | Inter | 0.875rem (14px) | 500 | 1.4 |
| Code | JetBrains Mono | 0.875rem (14px) | 400 | 1.5 |

**Carga de fuentes**: Google Fonts vía `<link>` en `index.html` o `@font-face` local.

### 5.4 Espaciado

Basado en una escala de 4px:

| Token | Valor | Uso |
|---|---|---|
| `--space-0` | 0 | Sin espaciado |
| `--space-1` | 4px | Espaciado mínimo (iconos) |
| `--space-2` | 8px | Espaciado pequeño (padding inputs) |
| `--space-3` | 12px | Espaciado entre elementos relacionados |
| `--space-4` | 16px | Espaciado base (padding cards) |
| `--space-6` | 24px | Espaciado entre secciones |
| `--space-8` | 32px | Espaciado entre bloques |
| `--space-12` | 48px | Espaciado grande |
| `--space-16` | 64px | Espaciado de página |

### 5.5 Bordes y Radios

| Token | Valor | Uso |
|---|---|---|
| `--radius-sm` | 4px | Badges, tags |
| `--radius-md` | 8px | Inputs, botones |
| `--radius-lg` | 12px | Cards, modales |
| `--radius-full` | 9999px | Avatares, pills |
| `--border-width` | 1px | Bordes estándar |
| `--border-width-thick` | 2px | Bordes enfocados |

### 5.6 Sombras

| Token | Valor | Uso |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Cards sutiles |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards elevadas, dropdowns |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modales, popovers |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Overlays |

### 5.7 Componentes Clave

#### Botones

| Variante | Background | Text | Border |
|---|---|---|---|
| Primary | `--color-primary` | `#FFFFFF` | none |
| Primary Hover | `--color-primary-dark` | `#FFFFFF` | none |
| Secondary | transparent | `--color-primary` | `--color-primary` |
| Ghost | transparent | `--color-text-secondary` | none |
| Danger | `--color-error` | `#FFFFFF` | none |

**Tamaños**: sm (32px height), md (40px height), lg (48px height)

#### Inputs

- Altura: 40px (md), 32px (sm)
- Border: 1px solid `--color-border`
- Border focus: 2px solid `--color-primary`
- Background: `--color-bg`
- Padding: 8px 12px

#### Cards

- Background: `--color-bg-secondary`
- Border: 1px solid `--color-border`
- Radius: `--radius-lg` (12px)
- Padding: 24px (`--space-6`)
- Shadow: `--shadow-sm`

#### Tabla de Cotización

- Header: Background `--color-primary`, text `#FFFFFF`
- Rows alternadas: `--color-bg` y `--color-bg-secondary`
- Disponible: texto en `--color-success`
- No disponible: texto en `--color-error`
- Precio competencia: badge `--color-warning` con margen 5%

### 5.8 Archivo HTML de Referencia

Se mantendrá un archivo HTML con todos los estilos del design system en:

```
FRONTEND/public/design-system.html
```

Este archivo contendrá:
- Muestra de todos los colores con sus tokens
- Tipografía en todos los tamaños
- Componentes visuales (botones, inputs, cards, badges, tabs, modales)
- Estados (hover, focus, disabled, error)
- Tabla de cotización de ejemplo
- Modo claro y modo oscuro lado a lado

Sirve como referencia visual única para que el equipo de frontend implemente los componentes de forma consistente.

### 5.9 Variables CSS (TailwindCSS)

Las variables se definen en `FRONTEND/src/styles/globals.css` y se consumen vía TailwindCSS:

```css
:root {
  /* Colores primarios */
  --color-primary: #0F4C75;
  --color-primary-dark: #0A3450;
  --color-primary-light: #3282B8;
  --color-primary-lighter: #BBE1FA;

  /* Colores de estado */
  --color-success: #16A34A;
  --color-success-light: #DCFCE7;
  --color-warning: #F59E0B;
  --color-warning-light: #FEF3C7;
  --color-error: #DC2626;
  --color-error-light: #FEE2E2;
  --color-info: #0EA5E9;
  --color-info-light: #E0F2FE;

  /* Neutros - Modo claro */
  --color-bg: #FFFFFF;
  --color-bg-secondary: #F8FAFC;
  --color-bg-tertiary: #F1F5F9;
  --color-border: #E2E8F0;
  --color-text: #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted: #94A3B8;

  /* Tipografía */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Espaciado */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;
  --space-16: 64px;

  /* Radios */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  /* Sombras */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.15);
}

.dark {
  --color-bg: #0F172A;
  --color-bg-secondary: #1E293B;
  --color-bg-tertiary: #334155;
  --color-border: #475569;
  --color-text: #F1F5F9;
  --color-text-secondary: #CBD5E1;
  --color-text-muted: #64748B;
}
```

---

## 6. API REST — Endpoints

### 6.1 Convenciones

- **Base URL**: `/api/v1`
- **Formato**: JSON
- **Autenticación**: Bearer JWT (obligatorio en todos los endpoints excepto `/auth/login` y `/health`)
- **Errores**: Formato estándar (ver 6.3)
- **Paginación**: `?page=1&limit=20`
- **Versionado**: Por path (`/api/v1/`)

### 6.2 Endpoints

#### Autenticación

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Iniciar sesión, devuelve JWT | No |
| `GET` | `/api/v1/auth/me` | Datos del usuario autenticado | Sí |
| `POST` | `/api/v1/auth/refresh` | Renovar token JWT | Sí |

**POST `/api/v1/auth/login`**

**Request**:
```json
{
  "email": "admin@cotia.com",
  "password": "Admin123!"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@cotia.com",
    "rol": "admin",
    "activo": true
  }
}
```

**Response 401**:
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Email o contraseña incorrectos"
  }
}
```

**Response 403** (usuario desactivado):
```json
{
  "error": {
    "code": "USER_INACTIVE",
    "message": "El usuario está desactivado. Contacte al administrador."
  }
}
```

**GET `/api/v1/auth/me`**

**Response 200**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cotia.com",
  "rol": "admin",
  "activo": true,
  "created_at": "2026-07-31T12:00:00Z"
}
```

#### Gestión de Usuarios (solo admin)

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `GET` | `/api/v1/usuarios` | Listar usuarios (paginado) | admin |
| `POST` | `/api/v1/usuarios` | Crear nuevo usuario | admin |
| `PATCH` | `/api/v1/usuarios/{id}/toggle-active` | Activar/desactivar usuario | admin |
| `PATCH` | `/api/v1/usuarios/{id}/password` | Cambiar contraseña de usuario | admin |

**POST `/api/v1/usuarios`**

**Request**:
```json
{
  "username": "vendedor1",
  "email": "vendedor1@cotia.com",
  "password": "Vendedor123!",
  "rol": "user"
}
```

**Response 201**:
```json
{
  "id": 3,
  "username": "vendedor1",
  "email": "vendedor1@cotia.com",
  "rol": "user",
  "activo": true,
  "created_at": "2026-07-31T14:00:00Z"
}
```

**PATCH `/api/v1/usuarios/{id}/toggle-active`**

**Response 200**:
```json
{
  "id": 3,
  "username": "vendedor1",
  "activo": false,
  "message": "Usuario desactivado"
}
```

> **Nota**: El endpoint `toggle-active` **desactiva** al usuario (`activo = false`), **nunca lo elimina**. Un usuario desactivado no puede iniciar sesión. Se puede reactivar con el mismo endpoint.

#### Health Check

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `GET` | `/api/v1/health` | Estado del servidor | No |

**Response 200**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

#### Upload de Archivos

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `POST` | `/api/v1/upload` | Cargar archivo (audio/imagen/texto) | Sí |

**Request**: `multipart/form-data`

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `file` | File | Sí | Archivo a procesar |
| `tipo` | String | Sí | `audio`, `imagen`, `texto` |

**Response 201**:
```json
{
  "session_id": "uuid-1234",
  "componentes": [
    {
      "tipo": "resistencia",
      "valor": "220",
      "unidad": "ohm",
      "cantidad": 5,
      "ambiguo": false
    }
  ],
  "ambiguedades_detectadas": true,
  "total_componentes": 3
}
```

#### Preguntas Inteligentes

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `GET` | `/api/v1/preguntas/{session_id}` | Obtener preguntas pendientes | Sí |
| `POST` | `/api/v1/preguntas/{session_id}/respuestas` | Enviar respuestas | Sí |

**GET Response 200**:
```json
{
  "session_id": "uuid-1234",
  "preguntas": [
    {
      "id": 16,
      "categoria": "LED",
      "pregunta": "¿Qué color o colores de LED necesita?",
      "campo_a_desambiguar": "color",
      "componentes_afectados": [2, 3]
    }
  ],
  "total_preguntas": 2
}
```

**POST Request**:
```json
{
  "respuestas": [
    {
      "pregunta_id": 16,
      "respuesta": "Rojo"
    },
    {
      "pregunta_id": 17,
      "respuesta": "5mm"
    }
  ]
}
```

**POST Response 200**:
```json
{
  "session_id": "uuid-1234",
  "componentes_actualizados": true,
  "ambiguedades_restantes": 0
}
```

#### Cotización

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `POST` | `/api/v1/cotizacion/{session_id}` | Generar cotización | Sí |
| `GET` | `/api/v1/cotizacion/{session_id}` | Obtener cotización existente | Sí |
| `GET` | `/api/v1/cotizacion/{session_id}/pdf` | Descargar PDF | Sí |
| `GET` | `/api/v1/cotizacion/{session_id}/excel` | Descargar Excel | Sí |
| `GET` | `/api/v1/cotizaciones` | Listar cotizaciones (histórico) | Sí |

**POST Response 201**:
```json
{
  "session_id": "uuid-1234",
  "cotizacion_id": 1,
  "items": [
    {
      "producto": "Resistencia 220Ω 1/4W",
      "cantidad": 5,
      "proveedores": [
        {
          "tienda": "AV Electronics",
          "precio_unitario": 0.50,
          "disponible": true,
          "url": "https://avelectronics.cc/..."
        },
        {
          "tienda": "Megatronica",
          "precio_unitario": 0.55,
          "disponible": true,
          "url": "https://megatronica.cc/...",
          "margen_aplicado": 5,
          "precio_con_margen": 0.58
        }
      ]
    }
  ],
  "total": 12.90,
  "fecha_creacion": "2026-07-31T15:00:00Z"
}
```

#### Productos

| Método | Path | Descripción | Auth |
|---|---|---|---|
| `GET` | `/api/v1/productos` | Buscar productos | Sí |
| `GET` | `/api/v1/productos/{id}` | Detalle de producto | Sí |
| `GET` | `/api/v1/productos/{id}/equivalencias` | Equivalentes de un producto | Sí |

**GET `/api/v1/productos?query=arduino`**:
```json
{
  "resultados": [
    {
      "id": 1,
      "nombre": "Arduino UNO R3",
      "categoria": "tarjeta_desarrollo",
      "especificaciones": {
        "chip": "ATmega328P",
        "voltaje": "5V"
      }
    }
  ],
  "total": 1
}
```

### 6.3 Formato de Errores Estándar

Todos los errores siguen el mismo formato:

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "El archivo excede el tamaño máximo permitido de 25MB",
    "details": {
      "max_size_mb": 25,
      "received_size_mb": 35
    }
  }
}
```

**Códigos de error**:

| Code | HTTP Status | Descripción |
|---|---|---|
| `INVALID_FILE_TYPE` | 415 | Tipo de archivo no soportado |
| `FILE_TOO_LARGE` | 413 | Archivo excede tamaño máximo |
| `SESSION_NOT_FOUND` | 404 | Sesión no existe o expiró |
| `PROCESSING_ERROR` | 500 | Error en procesamiento de ingesta |
| `SCRAPING_ERROR` | 502 | Error en web scraping |
| `PRODUCT_NOT_FOUND` | 404 | Producto no encontrado |
| `VALIDATION_ERROR` | 422 | Error de validación de Pydantic |
| `RATE_LIMIT_EXCEEDED` | 429 | Demasiadas peticiones |
| `AMBIGUITIES_PENDING` | 409 | Hay ambigüedades sin resolver |
| `INVALID_CREDENTIALS` | 401 | Email o contraseña incorrectos |
| `USER_INACTIVE` | 403 | Usuario desactivado, no puede iniciar sesión |
| `TOKEN_EXPIRED` | 401 | Token JWT expirado |
| `TOKEN_INVALID` | 401 | Token JWT inválido |
| `FORBIDDEN` | 403 | No tiene permisos (requiere rol admin) |
| `USER_NOT_FOUND` | 404 | Usuario no encontrado |
| `EMAIL_ALREADY_EXISTS` | 409 | Email ya registrado |
| `USERNAME_ALREADY_EXISTS` | 409 | Username ya registrado |

---

## 7. Flujo Detallado de Cotización

```
1. CLIENTE ingresa a la aplicación web
   │
2. SISTEMA muestra pantalla de Login (email + contraseña)
   │  ├── Si no tiene JWT → debe autenticarse
   │  └── Si tiene JWT válido → salta al paso 4
   │
3. CLIENTE inicia sesión (POST /api/v1/auth/login)
   │  ├── Backend valida email + password (bcrypt)
   │  ├── Verifica que el usuario esté activo
   │  └── Devuelve JWT + datos del usuario (rol)
   │
4. SISTEMA muestra App Shell con tabs según el rol
   │  ├── admin: Carga | Preguntas | Cotización | Historial | Usuarios
   │  └── user:  Carga | Preguntas | Cotización | Historial
   │
5. CLIENTE carga archivo (audio, imagen o texto) con lista de componentes
   │  (drag & drop o selección manual)
   │
6. FRONTEND envía archivo al BACKEND via POST /api/v1/upload
   │  (Header: Authorization: Bearer <JWT>)
   │
7. BACKEND recibe el archivo y lo envía al Motor de Ingesta Multimodal
   │
8. MOTOR DE INGESTA procesa el archivo:
   │   ├── Si es audio → Whisper/STT → texto
   │   ├── Si es imagen → OCR → texto
   │   └── Si es texto → lectura directa
   │
9. NLP extrae entidades → lista estructurada de componentes (JSON)
   │
10. MOTOR DE MATCHING normaliza términos:
   │   ├── "foquito chiquito" → LED
   │   ├── "tablita blanca" → Protoboard
   │   ├── "resistencia de 220" → Resistencia 220Ω
   │   └── Detecta campos faltantes (color, tamaño, potencia, etc.)
   │
11. BACKEND crea sesión de cotización en PostgreSQL
   │
12. SISTEMA DE PREGUNTAS evalúa ambigüedades:
   │   ├── Si hay campos faltantes → selecciona preguntas del banco
   │   ├── Prioriza preguntas que resuelvan múltiples ambigüedades
   │   └── Devuelve preguntas al FRONTEND
   │
13. FRONTEND muestra preguntas al cliente (chat interactivo)
   │
14. CLIENTE responde las preguntas
   │  (POST /api/v1/preguntas/{session_id}/respuestas)
   │
15. BACKEND actualiza la lista de componentes con las respuestas
   │
16. CLIENTE confirma (o el BACKEND procede automáticamente si no hay ambigüedades)
   │  (POST /api/v1/cotizacion/{session_id})
   │
17. WEB SCRAPING ENGINE busca cada componente:
   │   ├── Verifica cache en PostgreSQL (¿fue consultado hace < 24h?)
   │   │   └── Si sí → usa datos cacheados
   │   │   └── Si no → hace scraping en tiendas
   │   ├── AV Electronics → precio + disponibilidad
   │   ├── Megatronica → precio + disponibilidad
   │   └── Electro Store → precio + disponibilidad
   │
18. GENERADOR DE COTIZACIONES:
   │   ├── Compara precios entre proveedores
   │   ├── Aplica margen del 5% sobre productos de competencia
   │   ├── Estructura la cotización con desglose por ítem
   │   └── Calcula subtotal y total
   │
19. BACKEND guarda la cotización en PostgreSQL
   │
20. FRONTEND muestra la cotización al cliente:
   │   ├── Tabla con cada componente, proveedor, precio, disponibilidad
   │   ├── Cliente puede seleccionar/deseleccionar ítems
   │   └── Cliente puede descargar en PDF o Excel
   │
21. FIN DEL FLUJO
```

---

## 8. Modelo de Datos — Esquema de Tablas

### 8.1 Tabla `usuarios`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador único |
| `username` | VARCHAR(50) NOT NULL UNIQUE | Nombre de usuario |
| `email` | VARCHAR(255) NOT NULL UNIQUE | Email del usuario |
| `password_hash` | VARCHAR(255) NOT NULL | Hash bcrypt de la contraseña |
| `rol` | VARCHAR(20) NOT NULL DEFAULT 'user' | `admin` o `user` |
| `activo` | BOOLEAN DEFAULT true | Usuario activo (se desactiva, no se elimina) |
| `created_at` | TIMESTAMP DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP DEFAULT NOW() | Fecha de actualización |

**Índices**: `CREATE UNIQUE INDEX idx_usuarios_email ON usuarios(email);`
**Índices**: `CREATE UNIQUE INDEX idx_usuarios_username ON usuarios(username);`

**Seed inicial** (se ejecuta automáticamente al crear la BD):
```sql
INSERT INTO usuarios (username, email, password_hash, rol, activo) VALUES
  ('admin', 'admin@cotia.com', '<bcrypt_hash_Admin123!>', 'admin', true),
  ('user', 'user@cotia.com', '<bcrypt_hash_User123!>', 'user', true);
```

> **Importante**: Los usuarios **nunca se eliminan**. El admin los **desactiva** (`activo = false`). Un usuario desactivado no puede iniciar sesión.

### 8.2 Tabla `productos`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador único |
| `nombre` | VARCHAR(255) NOT NULL | Nombre normalizado del producto |
| `categoria` | VARCHAR(100) NOT NULL | Categoría (resistencia, capacitor, LED, etc.) |
| `especificaciones` | JSONB | Especificaciones técnicas (valor, unidad, potencia, etc.) |
| `terminos_coloniales` | TEXT[] | Términos coloquiales asociados |
| `activo` | BOOLEAN DEFAULT true | Producto activo en catálogo |
| `created_at` | TIMESTAMP DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP DEFAULT NOW() | Fecha de actualización |

**Índices**: `CREATE INDEX idx_productos_nombre ON productos(nombre);`
**Índices**: `CREATE INDEX idx_productos_categoria ON productos(categoria);`

### 8.3 Tabla `equivalencias`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | SERIAL PK | Identificador único |
| `producto_id` | INT FK → productos(id) | Producto de referencia |
| `termino_equivalente` | VARCHAR(255) NOT NULL | Término equivalente o sinónimo |
| `tipo_match` | VARCHAR(50) NOT NULL | `sinonimo`, `equivalencia_tecnica`, `coloquial` |
| `confianza` | FLOAT DEFAULT 1.0 | Nivel de confianza del match (0-1) |
| `created_at` | TIMESTAMP DEFAULT NOW() | Fecha de creación |

**Índices**: `CREATE INDEX idx_equivalencias_termino ON equivalencias(termino_equivalente);`

### 8.4 Tabla `cotizaciones`

| Columna               | Tipo                            | Descripción                            |
| -----------------------| ---------------------------------| ----------------------------------------|
| `id`                  | SERIAL PK                       | Identificador único                    |
| `session_id`          | UUID NOT NULL UNIQUE            | Sesión de la cotización                |
| `usuario_id`          | INT FK → usuarios(id) NOT NULL  | Usuario que creó la cotización         |
| `cliente_nombre`      | VARCHAR(255)                    | Nombre del cliente (opcional)          |
| `fecha_creacion`      | TIMESTAMP DEFAULT NOW()         | Fecha de creación                      |
| `fecha_actualizacion` | TIMESTAMP DEFAULT NOW()         | Fecha de última actualización          |
| `estado`              | VARCHAR(20) DEFAULT 'pendiente' | `pendiente`, `completada`, `cancelada` |
| `total`               | DECIMAL(10,2)                   | Total de la cotización                 |

**Índices**: `CREATE INDEX idx_cotizaciones_usuario ON cotizaciones(usuario_id);`

### 8.5 Tabla `cotizacion_items`

| Columna           | Tipo                      | Descripción                                   |
| -------------------| ---------------------------| -----------------------------------------------|
| `id`              | SERIAL PK                 | Identificador único                           |
| `cotizacion_id`   | INT FK → cotizaciones(id) | Cotización a la que pertenece                 |
| `producto_id`     | INT FK → productos(id)    | Producto cotizado                             |
| `cantidad`        | INT NOT NULL              | Cantidad solicitada                           |
| `precio_unitario` | DECIMAL(10,2) NOT NULL    | Precio por unidad                             |
| `proveedor`       | VARCHAR(100) NOT NULL     | Tienda proveedora                             |
| `margen_aplicado` | DECIMAL(5,2) DEFAULT 0    | Margen aplicado (0% o 5%)                     |
| `subtotal`        | DECIMAL(10,2) NOT NULL    | cantidad × precio_unitario                    |
| `disponible`      | BOOLEAN DEFAULT true      | Disponibilidad en el momento de la cotización |

### 8.6 Tabla `scraping_cache`

| Columna          | Tipo                    | Descripción                   |
| ------------------| -------------------------| -------------------------------|
| `id`             | SERIAL PK               | Identificador único           |
| `producto_id`    | INT FK → productos(id)  | Producto consultado           |
| `tienda`         | VARCHAR(100) NOT NULL   | Nombre de la tienda           |
| `precio`         | DECIMAL(10,2)           | Precio encontrado             |
| `disponible`     | BOOLEAN                 | Disponibilidad                |
| `url_producto`   | TEXT                    | URL del producto en la tienda |
| `fecha_consulta` | TIMESTAMP DEFAULT NOW() | Fecha de la última consulta   |
| `ttl_horas`      | INT DEFAULT 24          | TTL del cache en horas        |

**Índices**: `CREATE INDEX idx_scraping_cache_producto_tienda ON scraping_cache(producto_id, tienda);`

### 8.7 Tabla `banco_preguntas`

| Columna               | Tipo                  | Descripción                              |
| -----------------------| -----------------------| ------------------------------------------|
| `id`                  | SERIAL PK             | Identificador único                      |
| `categoria`           | VARCHAR(100) NOT NULL | Categoría de la pregunta                 |
| `pregunta`            | TEXT NOT NULL         | Texto de la pregunta                     |
| `campo_a_desambiguar` | VARCHAR(100)          | Campo que resuelve (color, tamaño, etc.) |
| `prioridad`           | INT DEFAULT 5         | Prioridad (1 = alta, 10 = baja)          |
| `activa`              | BOOLEAN DEFAULT true  | Pregunta activa                          |

### 8.8 Tabla `tiendas`

| Columna                   | Tipo                  | Descripción                             |
| ---------------------------| -----------------------| -----------------------------------------|
| `id`                      | SERIAL PK             | Identificador único                     |
| `nombre`                  | VARCHAR(100) NOT NULL | Nombre de la tienda                     |
| `url_base`                | TEXT NOT NULL         | URL base del sitio                      |
| `selector_precio`         | TEXT                  | Selector CSS para precio                |
| `selector_disponibilidad` | TEXT                  | Selector CSS para disponibilidad        |
| `selector_nombre`         | TEXT                  | Selector CSS para nombre de producto    |
| `activa`                  | BOOLEAN DEFAULT true  | Tienda activa para scraping             |
| `usa_javascript`          | BOOLEAN DEFAULT false | Si requiere renderizado JS (Playwright) |

### 8.9 Tabla `sesiones`

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | UUID PK | Identificador de sesión |
| `usuario_id` | INT FK → usuarios(id) NOT NULL | Usuario propietario de la sesión |
| `componentes_json` | JSONB | Lista de componentes extraídos |
| `ambiguedades_resueltas` | BOOLEAN DEFAULT false | Si se resolvieron todas las ambigüedades |
| `estado` | VARCHAR(20) DEFAULT 'activa' | `activa`, `procesando`, `completada`, `expirada` |
| `created_at` | TIMESTAMP DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP DEFAULT NOW() | Fecha de actualización |

**Índices**: `CREATE INDEX idx_sesiones_usuario ON sesiones(usuario_id);`

---

## 9. Docker y Despliegue

### 9.1 Arquitectura de Contenedores

```
docker-compose.yml
├── frontend      (Node 24 → Vite dev)        :5173
├── backend       (Python 3.14 → Uvicorn)    :8000
├── postgres      (PostgreSQL 16)            :5432
├── pgadmin       (pgAdmin 4)                :5050
├── redis         (Redis 7)                  :6379
└── celery-worker (Python 3.14 → Celery)     (sin puerto)
```

### 9.2 `docker-compose.yml` (raíz del proyecto)

```yaml
version: '3.8'

services:
  # ─── Base de Datos ───
  postgres:
    image: postgres:16-alpine
    container_name: cotia_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-cotia}
      POSTGRES_USER: ${POSTGRES_USER:-cotia_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cotia_pass}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-cotia_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── pgAdmin (Admin de PostgreSQL) ───
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: cotia_pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@cotia.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
      PGADMIN_CONFIG_SERVER_MODE: 'False'
    ports:
      - "5050:80"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - pgadmin_data:/var/lib/pgadmin

  # ─── Redis ───
  redis:
    image: redis:7-alpine
    container_name: cotia_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── Backend (FastAPI) ───
  backend:
    build:
      context: ./BACKEND
      dockerfile: Dockerfile
    container_name: cotia_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - ./BACKEND/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./BACKEND/app:/app/app
      - uploads_data:/app/uploads
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8000
      --reload

  # ─── Celery Worker (scraping programado) ───
  celery-worker:
    build:
      context: ./BACKEND
      dockerfile: Dockerfile
    container_name: cotia_celery
    restart: unless-stopped
    env_file:
      - ./BACKEND/.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./BACKEND/app:/app/app
    command: celery -A app.services.scraping.celery_app worker --loglevel=info

  # ─── Frontend (Vite dev server) ───
  frontend:
    build:
      context: ./FRONTEND
      dockerfile: Dockerfile
    container_name: cotia_frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    env_file:
      - ./FRONTEND/.env
    depends_on:
      - backend
    volumes:
      - ./FRONTEND/src:/app/src
      - ./FRONTEND/public:/app/public
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
  redis_data:
  uploads_data:
  pgadmin_data:
```

### 9.3 `BACKEND/Dockerfile`

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la aplicación
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando por defecto (override en docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.4 `FRONTEND/Dockerfile`

```dockerfile
FROM node:24-alpine

WORKDIR /app

# Dependencias
COPY package.json package-lock.json ./
RUN npm ci

# Código de la aplicación
COPY . .

# Exponer puerto de Vite
EXPOSE 5173

# Comando por defecto (override en docker-compose)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 9.5 Variables de Entorno

#### `BACKEND/.env.example`

```env
# ─── Base de Datos ───
POSTGRES_DB=cotia
POSTGRES_USER=cotia_user
POSTGRES_PASSWORD=cotia_pass
DATABASE_URL=postgresql+asyncpg://cotia_user:cotia_pass@postgres:5432/cotia

# ─── Redis ───
REDIS_URL=redis://redis:6379/0

# ─── APIs Externas ───
OPENAI_API_KEY=your_openai_api_key
WHISPER_API_KEY=your_whisper_api_key
GOOGLE_VISION_API_KEY=your_google_vision_api_key

# ─── Configuración ───
SCRAPING_TTL_HOURS=24
MARGEN_COMPETENCIA=5
MAX_FILE_SIZE_MB=25
CORS_ORIGINS=http://localhost:5173
SECRET_KEY=your_secret_key_here
ENVIRONMENT=development

# ─── Autenticación JWT ───
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
BCRYPT_COST_FACTOR=12

# ─── Celery ───
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ─── pgAdmin ───
PGADMIN_EMAIL=admin@cotia.com
PGADMIN_PASSWORD=admin
```

#### `FRONTEND/.env.example`

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=CotIA
VITE_APP_VERSION=1.0.0
```

### 9.6 Comandos de Gestión

```bash
# Levantar todos los servicios
docker-compose up -d

# Levantar con logs en vivo
docker-compose up

# Reconstruir imágenes
docker-compose up -d --build

# Detener todos los servicios
docker-compose down

# Detener y borrar volúmenes (¡cuidado! borra datos)
docker-compose down -v

# Ver logs de un servicio específico
docker-compose logs -f backend
docker-compose logs -f frontend

# Ejecutar migraciones de Alembic
docker-compose exec backend alembic upgrade head

# Crear nueva migración
docker-compose exec backend alembic revision --autogenerate -m "descripcion"

# Abrir shell de PostgreSQL
docker-compose exec postgres psql -U cotia_user -d cotia

# Abrir Redis CLI
docker-compose exec redis redis-cli

# Abrir pgAdmin en el navegador
#   http://localhost:5050
#   Usuario: admin@cotia.com  |  Contraseña: admin
#   Agregar servidor: Host=db, Port=5432, User=cotia_user, Password=cotia_pass

# Ejecutar tests del backend
docker-compose exec backend pytest

# Ejecutar tests del frontend
docker-compose exec frontend npm run test
```

### 9.7 Producción

Para producción se usan los mismos contenedores con ajustes:

- **Frontend**: Build estático servido por Nginx (no Vite dev server)
- **Backend**: Uvicorn con `--workers 4` (sin `--reload`)
- **PostgreSQL**: Persistencia garantizada con volumen nombrado
- **Variables**: `.env` de producción sin secretos en el repo

```bash
# Build de producción
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 10. Buenas Prácticas

### 10.1 Git y Control de Versiones

#### Convención de Commits (Conventional Commits)

```
<tipo>(<scope>): <descripción>

<cuerpo opcional>

<footer opcional>
```

**Tipos**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formato (no afecta lógica)
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Tareas de mantenimiento
- `ci`: CI/CD

**Ejemplos**:
```
feat(scraping): agregar scraper para Electro Store
fix(cotizacion): corregir cálculo de margen del 5%
docs(arquitectura): actualizar diagrama de componentes
test(matching): agregar tests para normalizador de unidades
```

#### Branching Strategy (Git Flow simplificado)

```
main          ────●─────●─────●─────●───── (producción)
                   │     │     │
develop       ─────●─────●─────●─────●─── (integración)
                   │           │
feature/xxx   ─────●─────●───── (rama temporal)
                         │
fix/yyy       ───────────●───── (rama temporal)
```

- `main`: Solo merges desde `develop` vía PR
- `develop`: Rama de integración
- `feature/*`: Ramas para nuevas funcionalidades
- `fix/*`: Ramas para correcciones
- **Regla**: Nunca hacer push directo a `main`

#### Reglas de PR

- Mínimo 1 revisor antes de merge
- Tests deben pasar en CI
- Linting debe pasar sin errores
- Descripción clara del cambio

### 10.2 Calidad de Código

#### Backend (Python)

- **Linter**: Ruff (reemplaza flake8 + isort)
- **Formateador**: Black
- **Type checking**: mypy (strict mode)
- **Import order**: isort (integrado en Ruff)
- **Docstrings**: Todas las funciones públicas con docstring estilo Google

```python
def normalizar_termino(termino: str) -> dict:
    """Normaliza un término coloquial a un producto estandarizado.

    Args:
        termino: Término coloquial ingresado por el usuario.

    Returns:
        Diccionario con el producto normalizado y nivel de confianza.

    Raises:
        ValueError: Si el término está vacío.
    """
    ...
```

**Configuración** (`BACKEND/pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.black]
line-length = 100
target-version = ["py314"]

[tool.mypy]
python_version = "3.14"
strict = true
```

#### Frontend (TypeScript)

- **Linter**: ESLint + @typescript-eslint
- **Formateador**: Prettier
- **Type checking**: TypeScript strict mode
- **Imports**: Absolute paths (`@/components/...`)

**Configuración** (`FRONTEND/.eslintrc.cjs`):
```js
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  rules: {
    'react/react-in-jsx-scope': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
};
```

### 10.3 Seguridad

- **Variables de entorno**: Nunca commitear `.env` real, solo `.env.example`
- **Secretos**: Usar Docker secrets o variables de entorno en producción
- **Validación de inputs**: Pydantic en backend, Zod en frontend
- **Sanitización**: Prevenir SQL injection (SQLAlchemy parametrizado), XSS (React escapa por defecto)
- **CORS**: Restringir orígenes permitidos
- **Rate limiting**: FastAPI middleware (slowapi o custom)
- **HTTPS**: En producción, siempre TLS
- **Headers de seguridad**: HSTS, X-Content-Type-Options, X-Frame-Options
- **Dependencias**: `pip-audit` (Python) y `npm audit` (Node) en CI

#### Autenticación y Autorización

- **JWT**: Token con expiración de 1 hora (configurable)
- **Hash de passwords**: bcrypt con cost factor 12 (passlib)
- **Refresh token**: Endpoint `/auth/refresh` para renovar sin re-login
- **Middleware de roles**: Dependencia de FastAPI que valida `rol == "admin"` en endpoints protegidos
- **Usuarios desactivados**: No se eliminan, se desactivan (`activo = false`). Login rechazado si `activo = false`
- **Logout**: Cliente elimina JWT del localStorage/state, backend opcionalmente blacklista el token en Redis
- **Password por defecto**: Las contraseñas iniciales (`Admin123!`, `User123!`) deben cambiarse en el primer login
- **Seed de BD**: Los usuarios por defecto se crean automáticamente en la primera migración de Alembic

### 10.4 Performance

- **Backend**:
  - Async/await en todas las operaciones I/O (DB, scraping, APIs)
  - Pool de conexiones SQLAlchemy (tamaño configurable)
  - Cache en Redis para respuestas frecuentes de LLM
  - Paginación en endpoints de listado
- **Frontend**:
  - Lazy loading de rutas (React.lazy + Suspense)
  - Memoización con useMemo y React.memo
  - Debounce en inputs de búsqueda
  - Compresión de assets en build (Vite automático)
- **Base de Datos**:
  - Índices en columnas de búsqueda frecuente
  - EXPLAIN ANALYZE en queries complejas
  - JSONB con GIN index para especificaciones

### 10.5 Logging y Monitoreo

- **Backend**: structlog con formato JSON en producción
- **Niveles**: DEBUG (dev), INFO (prod), WARNING, ERROR
- **Contexto**: session_id en cada log de cotización
- **Frontend**: Error boundaries + envío de errores a servicio de tracking
- **Health check**: Endpoint `/api/v1/health` con estado de DB y Redis

### 10.6 Manejo de Errores

- **Backend**: Middleware global de FastAPI para capturar excepciones no manejadas
- **Frontend**: Error boundaries de React + toast notifications
- **Scraping**: Try/catch por tienda, continuar con las demás si una falla
- **APIs externas**: Retry con backoff exponencial (máximo 3 intentos)
- **Timeouts**: Configurables por servicio (DB: 30s, Scraping: 30s, LLM: 60s)

### 10.7 Documentación

- **API**: OpenAPI/Swagger automático en `/docs` (FastAPI)
- **Código**: Docstrings en Python, JSDoc/TSDoc en TypeScript
- **README**: Instrucciones de setup, comandos Docker, troubleshooting
- **Arquitectura**: Este documento, mantenido actualizado

---

## 11. Estrategia de Testing

### 11.1 Pirámide de Tests

```
           ┌───────────┐
           │    E2E    │     ← Pocos, flujos completos (Playwright)
           └───────────┘
         ┌───────────────┐
         │  Integración   │    ← API + DB + Redis (pytest + httpx)
         └───────────────┘
       ┌───────────────────┐
       │     Unitarios      │  ← Funciones puras, servicios (pytest, Vitest)
       └───────────────────┘
```

### 11.2 Backend (pytest)

| Tipo | Herramienta | Cobertura mínima |
|---|---|---|
| Unitarios | pytest + pytest-asyncio | 80% |
| Integración | pytest + httpx + test DB | 60% |
| Fixtures | pytest fixtures | — |
| Mocking | pytest-mock / unittest.mock | — |

**Tests clave**:
- `test_auth.py`: Login válido, login inválido, usuario desactivado, token expirado, refresh token
- `test_usuarios.py`: Crear usuario, desactivar usuario, reactivar usuario, permisos admin
- `test_upload.py`: Carga de archivos por tipo, validación de tamaño, formato
- `test_matching.py`: Normalización de términos, equivalencias, detección de ambigüedades
- `test_scraping.py`: Scrapers con HTML mock, cache, manejo de errores
- `test_cotizacion.py`: Generación de cotización, cálculo de margen, exportación
- `test_preguntas.py`: Selección de preguntas, detección de ambigüedades

**Comando**:
```bash
docker-compose exec backend pytest --cov=app --cov-report=term-missing
```

### 11.3 Frontend (Vitest)

| Tipo | Herramienta | Cobertura mínima |
|---|---|---|
| Unitarios | Vitest | 70% |
| Componentes | Testing Library | — |
| Mocking | MSW (Mock Service Worker) | — |

**Tests clave**:
- Componentes UI: renderizado, props, estados
- Páginas: flujo básico, rendering condicional
- Services: llamadas a API con mocks
- Store: estado de cotización

**Comando**:
```bash
docker-compose exec frontend npm run test -- --coverage
```

### 11.4 CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: pip install -r BACKEND/requirements.txt -r BACKEND/requirements-dev.txt
      - name: Lint
        run: ruff check BACKEND/app/
      - name: Type check
        run: mypy BACKEND/app/
      - name: Tests
        run: pytest BACKEND/tests/ --cov=BACKEND/app --cov-report=xml

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '24'
      - name: Install dependencies
        run: cd FRONTEND && npm ci
      - name: Lint
        run: cd FRONTEND && npm run lint
      - name: Type check
        run: cd FRONTEND && npx tsc --noEmit
      - name: Tests
        run: cd FRONTEND && npm run test -- --coverage
```

---

## 12. Estructura del Repositorio

```
repost/
├── BACKEND/
│   ├── app/
│   │   ├── main.py                  # Entry point FastAPI
│   │   ├── core/
│   │   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   │   ├── database.py          # Conexión SQLAlchemy async
│   │   │   ├── security.py          # JWT, CORS, rate limiting
│   │   │   └── logging.py           # Configuración de logging
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py        # Router principal
│   │   │       └── endpoints/
│   │   │           ├── auth.py       # Login, me, refresh
│   │   │           ├── usuarios.py   # CRUD usuarios (solo admin)
│   │   │           ├── upload.py
│   │   │           ├── cotizacion.py
│   │   │           ├── preguntas.py
│   │   │           ├── productos.py
│   │   │           └── health.py
│   │   ├── models/                  # Modelos SQLAlchemy (incl. usuario.py)
│   │   ├── schemas/                 # Schemas Pydantic (incl. auth.py, usuario.py)
│   │   ├── services/
│   │   │   ├── ingesta/             # Motor de ingesta multimodal
│   │   │   ├── matching/            # Motor de matching inteligente
│   │   │   ├── preguntas/           # Sistema de preguntas inteligentes
│   │   │   ├── scraping/            # Web scraping engine
│   │   │   └── cotizacion/          # Generador de cotizaciones
│   │   └── utils/
│   ├── alembic/                     # Migraciones
│   ├── tests/
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml               # Ruff, Black, mypy config
│
├── FRONTEND/
│   ├── public/
│   │   ├── design-system.html       # Guía visual de estilos (HTML)
│   │   ├── favicon.ico
│   │   └── logo.svg
│   ├── src/
│   │   ├── app/                     # App shell y layout global
│   │   │   ├── App.tsx              # Root component
│   │   │   ├── AppShell.tsx         # Layout: Header + Content + Footer
│   │   │   ├── AppRouter.tsx        # Router con lazy loading por módulo
│   │   │   └── AppProviders.tsx     # Providers (theme, toast, etc.)
│   │   ├── modules/                # Módulos de la aplicación
│   │   │   ├── login/              # Módulo Login (pantalla inicial)
│   │   │   ├── header/             # Módulo Header (global)
│   │   │   ├── footer/             # Módulo Footer (global)
│   │   │   ├── carga/              # Módulo Carga (Tab 1)
│   │   │   ├── preguntas/          # Módulo Preguntas (Tab 2)
│   │   │   ├── cotizacion/         # Módulo Cotización (Tab 3)
│   │   │   ├── historial/          # Módulo Historial (Tab 4)
│   │   │   └── usuarios/          # Módulo Gestión Usuarios (Tab 5 - admin)
│   │   ├── shared/                 # Recursos compartidos
│   │   │   ├── components/         # UI base (shadcn/ui + common)
│   │   │   ├── lib/               # api.ts, utils.ts, constants.ts
│   │   │   ├── store/             # Zustand stores globales
│   │   │   ├── types/             # Tipos TypeScript compartidos
│   │   │   └── hooks/             # Hooks compartidos (useTheme, etc.)
│   │   ├── styles/
│   │   │   └── globals.css        # Tailwind + variables CSS
│   │   └── main.tsx               # Entry point
│   ├── .env.example
│   ├── .eslintrc.cjs
│   ├── .prettierrc
│   ├── Dockerfile
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── instructivo/
│   ├── arquitectura.md              # Este documento
│   ├── levantamiento.md            # Levantamiento de información
│   └── Proyecto-IA/                # Material de referencia
│       ├── Decopy-VID...txt        # Transcripción del video
│       ├── preguntas.txt           # Banco de preguntas
│       ├── web.docx                # Enlaces de tiendas
│       ├── PreguntasJQ.pdf         # Preguntas reales de clientes
│       ├── preguntas_10_GD.pdf     # Preguntas técnicas con respuestas
│       └── preguntas_clientes_electronica.pdf # Preguntas de mostrador
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # Pipeline CI/CD
│
├── docker-compose.yml              # Desarrollo
├── docker-compose.prod.yml         # Producción
├── .gitignore
└── README.md
```

---

## 13. Próximos Pasos

### Fase 1: Infraestructura base (Semana 1-2)

1. **Configurar Docker Compose** con PostgreSQL, Redis, pgAdmin, backend y frontend
2. **Crear estructura de carpetas** BACKEND y FRONTEND según sección 12
3. **Configurar FastAPI** con health check y CORS
4. **Configurar React + Vite** con TailwindCSS y design system
5. **Crear archivo HTML de design system** en `FRONTEND/public/design-system.html`
6. **Configurar Alembic** y crear migraciones iniciales (todas las tablas, incl. usuarios)
7. **Implementar autenticación**: JWT, bcrypt, endpoints de login/me/refresh, seed de usuarios por defecto
8. **Implementar módulo Login** en frontend (pantalla inicial, sin tabs)
9. **Implementar módulo Gestión de Usuarios** en frontend (solo admin: crear, desactivar)
10. **Configurar CI/CD** con GitHub Actions (lint + tests)

### Fase 2: Ingesta y Matching (Semana 3-4)

11. **Análisis de sitios web**: Inspeccionar HTML de AV Electronics, Megatronica y Electro Store
12. **Implementar Motor de Ingesta**: Empezar con texto → NLP → lista estructurada
13. **Implementar Motor de Matching**: Diccionario de equivalencias + normalización
14. **Implementar Sistema de Preguntas**: Detección de ambigüedades + selección del banco
15. **Tests unitarios** para matching y preguntas

### Fase 3: Scraping y Cotización (Semana 5-6)

16. **Implementar scraper base** (interfaz abstracta + cache)
17. **Implementar scraper** para una tienda (AV Electronics)
18. **Implementar scrapers** restantes (Megatronica, Electro Store)
19. **Implementar Comparador de Precios** con margen del 5%
20. **Implementar Generador de Cotizaciones** (PDF + Excel)
21. **Tests de integración** para scraping y cotización

### Fase 4: Frontend e Integración (Semana 7-8)

22. **Implementar página de carga** de archivos (drag & drop)
23. **Implementar chat de preguntas** interactivo
24. **Implementar tabla de cotización** con selección de proveedores
25. **Implementar descarga** de PDF y Excel
26. **Implementar historial** de cotizaciones
27. **Tests de componentes** frontend

### Fase 5: Despliegue y Pruebas (Semana 9-10)

28. **Configurar `docker-compose.prod.yml`** con Nginx para frontend
29. **Desplegar en servidor** (VPS o cloud)
30. **Pruebas con usuarios reales** con listas reales de componentes
31. **Ajustes finales** basados en feedback
32. **Documentación final** del README
