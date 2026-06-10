import { Links, Meta, Outlet, Scripts, ScrollRestoration, isRouteErrorResponse } from "react-router"

import type { Route } from "./+types/root"
import "./app.css"
import { Toaster } from "~/components/ui/sonner"
import { applyStoredTheme } from "~/lib/theme"

// SPA: aplica tema salvo o quanto antes (CSP bloqueia inline script).
applyStoredTheme()

const FAVICON =
  "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='%23c32a30' d='M12 2L2 7l10 5 10-5-10-5zm0 10L2 7v10l10 5 10-5V7l-10 5z'/></svg>"

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Sinalys — ERP de Orçamentação Viária</title>
        <link rel="icon" type="image/svg+xml" href={FAVICON} />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <Toaster position="bottom-right" richColors />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  )
}

export default function App() {
  return <Outlet />
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Ops!"
  let details = "Ocorreu um erro inesperado."
  let stack: string | undefined

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Erro"
    details =
      error.status === 404
        ? "A página solicitada não foi encontrada."
        : error.statusText || details
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message
    stack = error.stack
  }

  return (
    <main className="container mx-auto p-4 pt-16">
      <h1 className="text-2xl font-semibold">{message}</h1>
      <p className="text-muted-foreground mt-2">{details}</p>
      {stack && (
        <pre className="bg-muted mt-4 w-full overflow-x-auto p-4 text-xs">
          <code>{stack}</code>
        </pre>
      )}
    </main>
  )
}
