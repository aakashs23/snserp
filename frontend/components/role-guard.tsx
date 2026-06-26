"use client"

import { useEffect, useState } from "react"
import { useAuth } from "@/components/providers/auth-provider"
import { Lock } from "lucide-react"

interface RoleGuardProps {
  allowedRoles: string[]
  children: React.ReactNode
}

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const { roleName, isLoading } = useAuth()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted || isLoading) return null

  if (!roleName || !allowedRoles.includes(roleName)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center px-4">
        <div className="bg-muted p-4 rounded-full mb-4">
          <Lock className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-2xl font-bold font-[family-name:var(--font-heading)] mb-2">Access Denied</h2>
        <p className="text-muted-foreground max-w-md">
          You do not have the required permissions to view this page. If you believe this is a mistake, please contact your system administrator.
        </p>
      </div>
    )
  }

  return <>{children}</>
}
