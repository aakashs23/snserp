import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

/**
 * Build a per-request nonce-based Content-Security-Policy.
 *
 * script-src uses a nonce + strict-dynamic — the meaningful XSS defense. Next.js
 * automatically stamps this nonce onto its own inline hydration scripts once it
 * sees `nonce-` in the request's CSP header (that's why we forward it via
 * request headers below).
 *
 * style-src keeps 'unsafe-inline' because Recharts and Tailwind emit inline
 * style *attributes*, which nonces cannot cover. connect-src/img-src/frame-src
 * allow Supabase (auth, realtime wss, storage signed URLs) which the browser
 * talks to directly.
 */
function buildCsp(nonce: string): string {
  const isDev = process.env.NODE_ENV === 'development'
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? ''
  const supabaseWs = supabaseUrl.replace(/^http/, 'ws')

  const directives = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''}`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' blob: data: https:`,
    `font-src 'self'`,
    `connect-src 'self' ${supabaseUrl} ${supabaseWs}`,
    `frame-src 'self' blob: ${supabaseUrl}`,
    `worker-src 'self' blob:`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,
    // Only in production: on http://localhost this would force-upgrade the
    // same-origin /api proxy to https and break local dev.
    ...(isDev ? [] : [`upgrade-insecure-requests`]),
  ]
  return directives.join('; ')
}

export async function updateSession(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const csp = buildCsp(nonce)

  // Forward the nonce + CSP to the SSR render so Next stamps the nonce onto its
  // inline scripts. Must be set on the *request* headers passed to NextResponse.next.
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', csp)

  let supabaseResponse = NextResponse.next({
    request: { headers: requestHeaders },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request: { headers: requestHeaders },
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // refreshing the auth token
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const isApiRoute = request.nextUrl.pathname.startsWith('/api/')

  if (isApiRoute) {
    supabaseResponse.headers.set('Content-Security-Policy', csp)
    return supabaseResponse
  }

  // Protect private routes
  const isAuthRoute = request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/register'

  if (!user && !isAuthRoute) {
    // If no user and trying to access a private route, redirect to login
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    const redirect = NextResponse.redirect(url)
    redirect.headers.set('Content-Security-Policy', csp)
    return redirect
  }

  if (user && isAuthRoute) {
    // If user is already logged in and trying to access login/register, redirect to dashboard
    const url = request.nextUrl.clone()
    url.pathname = '/'
    const redirect = NextResponse.redirect(url)
    redirect.headers.set('Content-Security-Policy', csp)
    return redirect
  }

  supabaseResponse.headers.set('Content-Security-Policy', csp)
  return supabaseResponse
}
