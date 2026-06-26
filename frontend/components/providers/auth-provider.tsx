"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { createClient } from "@/utils/supabase/client"

interface Role {
  id: string
  name: string
  description: string | null
}

interface UserProfile {
  id: string
  full_name: string
  email: string
  role_id: string
  role: Role | null
  is_active: boolean
}

interface AuthContextType {
  user: UserProfile | null
  roleName: string | null
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  roleName: null,
  isLoading: true,
})

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [roleName, setRoleName] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    async function fetchUser() {
      try {
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()

        if (!session?.access_token) {
          if (isMounted) setIsLoading(false)
          return
        }

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${API_URL}/api/v1/auth/me`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
        })

        if (res.ok) {
          const profile: UserProfile = await res.json()
          if (isMounted) {
            setUser(profile)
            setRoleName(profile.role?.name || null)
          }
        }
      } catch (error) {
        console.error("Failed to fetch user profile", error)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    fetchUser()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, roleName, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
