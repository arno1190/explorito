# Explorito Frontend

A Next.js 15 application for discovering age-appropriate activities for children.

## Tech Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **TailwindCSS v4** - Styling
- **shadcn/ui** - UI component library
- **TanStack Query** - Data fetching and state management
- **Axios** - HTTP client
- **Lucide React** - Icons

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (recommended) or npm

### Installation

1. Install dependencies:

```bash
pnpm install
```

2. Create environment file:

```bash
cp .env.local.example .env.local
```

3. Update the environment variables in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Building for Production

```bash
pnpm build
pnpm start
```

## Project Structure

```
src/
├── app/
│   ├── (auth)/          # Authentication routes
│   │   ├── login/       # Login page
│   │   └── register/    # Registration page
│   ├── (app)/           # Protected app routes
│   │   └── dashboard/   # Dashboard page
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── providers.tsx    # App providers (Auth, Query)
├── components/
│   ├── layout/          # Layout components
│   │   ├── Header.tsx
│   │   └── ChildLayout.tsx
│   └── ui/              # shadcn/ui components
├── lib/
│   ├── api.ts           # API client and endpoints
│   ├── auth.tsx         # Auth context and hooks
│   └── utils.ts         # Utility functions
└── types/
    └── index.ts         # TypeScript type definitions
```

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: Manage children and view activities
- **Protected Routes**: Automatic redirection for authenticated users
- **Type-safe API**: Full TypeScript coverage for API calls
- **Responsive Design**: Mobile-first design with TailwindCSS

## Available Scripts

- `pnpm dev` - Start development server
- `pnpm build` - Build for production
- `pnpm start` - Start production server
- `pnpm lint` - Run ESLint
- `pnpm format` - Format code with Prettier

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## API Integration

The frontend communicates with the backend API using Axios. All API calls are centralized in `src/lib/api.ts` and include:

- Automatic token injection from localStorage
- 401 error handling with automatic logout
- Type-safe request/response interfaces

## Authentication Flow

1. User logs in via `/login` or registers via `/register`
2. JWT token is stored in localStorage
3. Token is automatically included in all API requests
4. Protected routes check authentication status
5. Unauthorized users are redirected to login

## Development Guidelines

### Code Style

- Use TypeScript for all new files
- Follow Next.js 15 App Router patterns
- Use Server Components by default, add `"use client"` only when needed
- Use shadcn/ui components from `@/components/ui`
- Use TanStack Query for data fetching
- Format code with Prettier before committing

### Adding New Components

Use shadcn CLI to add new components:

```bash
pnpm dlx shadcn@latest add [component-name]
```

### State Management

- **Global State**: React Context (Auth)
- **Server State**: TanStack Query
- **Local State**: useState/useReducer

## License

Private - All rights reserved
