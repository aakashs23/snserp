"use client"

import { useState, useEffect } from "react"
import { Settings as SettingsIcon, User as UserIcon, Mail, Phone, ShieldCheck } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

interface UserProfile {
  id: string
  full_name: string
  email: string
  phone: string | null
  avatar_url: string | null
  is_active: boolean
  role?: {
    name: string
    description: string
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchProfile() {
      try {
        const supabase = createClient()
        const { data: { session } } = await supabase.auth.getSession()

        const res = await fetch(`${API_URL}/api/v1/auth/me`, {
          headers: {
            "Authorization": `Bearer ${session?.access_token}`,
          }
        })

        if (res.ok) {
          setProfile(await res.json())
        } else {
          toast.error("Failed to load profile settings")
        }
      } catch {
        toast.error("Network error")
      } finally {
        setLoading(false)
      }
    }
    
    fetchProfile()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <Skeleton className="size-20 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-40" />
                <Skeleton className="h-4 w-32" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!profile) return <div>Failed to load settings.</div>

  const initials = profile.full_name?.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase() || "U"

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)] flex items-center gap-2">
          <SettingsIcon className="size-7 text-primary" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage your account profile and preferences.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
          <CardDescription>Your profile details used across the ERP system.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Avatar Section */}
          <div className="flex items-center gap-6">
            <Avatar className="size-24 border-4 border-background shadow-sm">
              <AvatarImage src={profile.avatar_url || ""} alt={profile.full_name} />
              <AvatarFallback className="text-2xl bg-primary text-primary-foreground">{initials}</AvatarFallback>
            </Avatar>
            <div>
              <h3 className="text-xl font-medium">{profile.full_name}</h3>
              <p className="text-sm text-muted-foreground">{profile.email}</p>
              <div className="flex items-center gap-1.5 mt-2">
                <ShieldCheck className="size-4 text-emerald-500" />
                <span className="text-xs font-medium uppercase tracking-wider text-emerald-500">
                  {profile.role?.name || "User"} Role
                </span>
              </div>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-muted-foreground">
                <UserIcon className="size-4" /> Full Name
              </Label>
              <Input value={profile.full_name} readOnly className="bg-muted/50" />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-muted-foreground">
                <Mail className="size-4" /> Email Address
              </Label>
              <Input value={profile.email} readOnly className="bg-muted/50" />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-muted-foreground">
                <Phone className="size-4" /> Phone Number
              </Label>
              <Input value={profile.phone || "Not provided"} readOnly className="bg-muted/50" />
            </div>
            
            <div className="space-y-2">
              <Label className="flex items-center gap-2 text-muted-foreground">
                <ShieldCheck className="size-4" /> Account Status
              </Label>
              <Input value={profile.is_active ? "Active" : "Inactive"} readOnly className="bg-muted/50 font-medium text-emerald-600" />
            </div>
          </div>
        </CardContent>
      </Card>
      
      <p className="text-center text-sm text-muted-foreground pt-4">
        To modify your profile details or change your password, please contact your system administrator.
      </p>
    </div>
  )
}
