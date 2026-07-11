'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'

/**
 * Verify a Cloudflare Turnstile token via the FastAPI backend (which holds the
 * secret). Returns true only on a confirmed pass; any error fails closed.
 */
async function verifyTurnstile(token: FormDataEntryValue | null): Promise<boolean> {
  if (!token || typeof token !== 'string') return false
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
  try {
    const res = await fetch(`${API_URL}/api/v1/auth/verify-turnstile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
      cache: 'no-store',
    })
    return res.ok
  } catch {
    return false
  }
}

export async function login(formData: FormData) {
  if (!(await verifyTurnstile(formData.get('cf-turnstile-response')))) {
    redirect('/login?error=' + encodeURIComponent('CAPTCHA verification failed. Please try again.'))
  }

  const supabase = await createClient()

  // type-casting here for convenience
  // in practice, you should validate your inputs
  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { data: authData, error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    redirect('/login?error=' + encodeURIComponent(error.message))
  }

  if (authData?.session) {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
    try {
      await fetch(`${API_URL}/api/v1/users/me/last-login`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${authData.session.access_token}`
        }
      })
      await fetch(`${API_URL}/api/v1/auth/log-login`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authData.session.access_token}`
        }
      })
    } catch (e) {
      console.error("Failed to update last login", e)
    }
  }

  revalidatePath('/', 'layout')
  redirect('/')
}

export async function signup(formData: FormData) {
  // Enforce the registration toggle on the operation, not just the page render.
  // Without this, a direct POST to this action creates an account regardless of
  // the flag. Defense-in-depth: also disable signups in the Supabase dashboard.
  if (process.env.ENABLE_REGISTRATION !== 'true') {
    redirect('/login')
  }

  if (!(await verifyTurnstile(formData.get('cf-turnstile-response')))) {
    redirect('/register?error=' + encodeURIComponent('CAPTCHA verification failed. Please try again.'))
  }

  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
    options: {
      data: {
        full_name: formData.get('full_name') as string,
      }
    }
  }

  const { error } = await supabase.auth.signUp(data)

  if (error) {
    redirect('/register?error=' + encodeURIComponent(error.message))
  }

  revalidatePath('/', 'layout')
  redirect('/')
}

export async function signout() {
  const supabase = await createClient()
  
  // Log logout before signing out locally
  const { data: { session } } = await supabase.auth.getSession()
  if (session) {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
    try {
      await fetch(`${API_URL}/api/v1/auth/log-logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })
    } catch (e) {
      console.error("Failed to log logout", e)
    }
  }

  await supabase.auth.signOut()
  revalidatePath('/', 'layout')
  redirect('/login')
}
