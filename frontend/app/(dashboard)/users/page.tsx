"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Pencil, Shield, CheckCircle2, XCircle, Trash2 } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { RoleGuard } from "@/components/role-guard"

interface Role {
  id: string
  name: string
  description: string
}

interface User {
  id: string
  full_name: string
  email: string
  role_id: string
  role: Role
  is_active: boolean
  last_login: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const headers = await getAuthHeaders()
      
      const [usersRes, rolesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/users`, { headers }),
        fetch(`${API_URL}/api/v1/users/roles`, { headers })
      ])
      
      if (usersRes.ok && rolesRes.ok) {
        const usersData = await usersRes.json()
        const rolesData = await rolesRes.json()
        setUsers(usersData)
        setRoles(rolesData)
      } else {
        toast.error("Failed to load users data")
      }
    } catch {
      toast.error("Network error fetching users")
    } finally {
      setLoading(false)
    }
  }, [getAuthHeaders])

  useEffect(() => {
    const t = setTimeout(() => fetchData(), 0)
    return () => clearTimeout(t)
  }, [fetchData])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    
    // Grab values directly from form
    const body: Record<string, any> = Object.fromEntries(formData.entries())

    // Convert switch value to boolean if editing
    if (editingUser) {
      body.is_active = formData.get('is_active') === 'on'
    }

    try {
      const headers = await getAuthHeaders()
      const url = editingUser
        ? `${API_URL}/api/v1/users/${editingUser.id}`
        : `${API_URL}/api/v1/users`
      const method = editingUser ? "PATCH" : "POST"

      const res = await fetch(url, { method, headers, body: JSON.stringify(body) })
      if (res.ok) {
        toast.success(editingUser ? "User updated successfully" : "User created successfully")
        setDialogOpen(false)
        setEditingUser(null)
        fetchData()
      } else {
        const err = await res.json()
        let errorMessage = "Operation failed."
        if (err.detail) {
          if (Array.isArray(err.detail)) {
            errorMessage = err.detail.map((e: any) => `${e.loc?.join('.')} - ${e.msg}`).join(", ")
          } else if (typeof err.detail === "string") {
            errorMessage = err.detail
          }
        }
        toast.error(errorMessage)
      }
    } catch {
      toast.error("Network error")
    }
  }

  const openEdit = (user: User) => {
    setEditingUser(user)
    setDialogOpen(true)
  }

  const openNew = () => {
    setEditingUser(null)
    setDialogOpen(true)
  }

  const handleDelete = async (user: User) => {
    if (!window.confirm(`Are you sure you want to permanently delete the user ${user.full_name}?`)) {
      return
    }

    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}`, {
        method: "DELETE",
        headers
      })

      if (res.ok) {
        toast.success("User deleted successfully")
        fetchData()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to delete user")
      }
    } catch {
      toast.error("Network error while deleting user")
    }
  }

  return (
    <RoleGuard allowedRoles={["admin"]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
              Users
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage system users, roles, and access.
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setEditingUser(null); }}>
            <DialogTrigger asChild>
              <Button onClick={openNew}>
                <Plus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[450px]">
              <form onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>{editingUser ? "Edit User" : "Add New User"}</DialogTitle>
                  <DialogDescription>
                    {editingUser ? "Update role and access status." : "Create a new user account and send them their password."}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  
                  {!editingUser && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="full_name">Full Name *</Label>
                        <Input id="full_name" name="full_name" required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="email">Email *</Label>
                        <Input id="email" name="email" type="email" required />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="password">Temporary Password *</Label>
                        <Input id="password" name="password" type="password" required minLength={6} />
                      </div>
                    </>
                  )}

                  {editingUser && (
                    <div className="space-y-2">
                      <Label>User</Label>
                      <div className="p-3 bg-muted rounded-md text-sm border">
                        <div className="font-medium">{editingUser.full_name}</div>
                        <div className="text-muted-foreground">{editingUser.email}</div>
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="role_id">Role *</Label>
                    <Select name="role_id" defaultValue={editingUser?.role_id} required>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map(role => (
                          <SelectItem key={role.id} value={role.id}>
                            {role.name.charAt(0).toUpperCase() + role.name.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {editingUser && (
                    <div className="flex items-center justify-between rounded-lg border p-4 mt-2">
                      <div className="space-y-0.5">
                        <Label className="text-base">Active Account</Label>
                        <p className="text-sm text-muted-foreground">
                          Turn off to disable the user&apos;s access.
                        </p>
                      </div>
                      <Switch
                        name="is_active"
                        defaultChecked={editingUser.is_active}
                      />
                    </div>
                  )}

                </div>
                <DialogFooter>
                  <Button type="submit">{editingUser ? "Save Changes" : "Create User"}</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell><Skeleton className="h-10 w-48" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell><Skeleton className="h-8 w-8 ml-auto" /></TableCell>
                    </TableRow>
                  ))
                ) : users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                      No users found.
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{user.full_name}</span>
                          <span className="text-sm text-muted-foreground">{user.email}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Shield className="h-3 w-3 text-primary" />
                          <span className="capitalize text-sm font-medium">
                            {user.role?.name || "Unknown"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                            <CheckCircle2 className="h-3 w-3" /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                            <XCircle className="h-3 w-3" /> Disabled
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {user.last_login ? new Date(user.last_login).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : "Never"}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end items-center gap-2">
                          <Button variant="outline" size="sm" onClick={() => openEdit(user)}>
                            <Pencil className="h-3.5 w-3.5 mr-2" />
                            Edit
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => handleDelete(user)}>
                            <Trash2 className="h-3.5 w-3.5 mr-2" />
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </RoleGuard>
  )
}