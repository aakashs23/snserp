"use client"

import { useState, useEffect, useCallback } from "react"
import { Shield, Trash2,  } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface DocumentPermission {
  id: string
  user_id: string
  can_view: boolean
  can_download: boolean
  can_edit: boolean
  user: {
    email: string
    full_name: string
  }
}

interface User {
  id: string
  email: string
  full_name: string
  role: {
    name: string
  }
}

export function DocumentPermissionsDialog({
  documentId,
  open,
  onOpenChange,
}: {
  documentId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [permissions, setPermissions] = useState<DocumentPermission[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedUserId, setSelectedUserId] = useState<string>("")
  const [canView, setCanView] = useState(true)
  const [canDownload, setCanDownload] = useState(false)
  const [canEdit, setCanEdit] = useState(false)

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchData = useCallback(async () => {
    if (!documentId || !open) return
    setLoading(true)
    try {
      const headers = await getAuthHeaders()
      
      const [permRes, usersRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/documents/${documentId}/permissions`, { headers }),
        fetch(`${API_URL}/api/v1/users`, { headers })
      ])
      
      if (permRes.ok) {
        setPermissions(await permRes.json())
      }
      if (usersRes.ok) {
        const allUsers: User[] = await usersRes.json()
        // Only accountant and viewer need explicit permissions
        setUsers(allUsers.filter(u => ["accountant", "viewer"].includes(u.role?.name)))
      }
    } catch {
      toast.error("Failed to load permissions")
    } finally {
      setLoading(false)
    }
  }, [documentId, open, getAuthHeaders])

  useEffect(() => {
    const t = setTimeout(() => fetchData(), 0)
    return () => clearTimeout(t)
  }, [fetchData])

  const handleGrant = async () => {
    if (!selectedUserId || !documentId) return
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/permissions`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_id: selectedUserId,
          can_view: canView,
          can_download: canDownload,
          can_edit: canEdit
        })
      })
      if (res.ok) {
        toast.success("Permission granted")
        fetchData()
        setSelectedUserId("")
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to grant permission")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handleUpdate = async (userId: string, updates: Partial<DocumentPermission>) => {
    if (!documentId) return
    const perm = permissions.find(p => p.user_id === userId)
    if (!perm) return
    
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/permissions/${userId}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({
          can_view: updates.can_view ?? perm.can_view,
          can_download: updates.can_download ?? perm.can_download,
          can_edit: updates.can_edit ?? perm.can_edit,
        })
      })
      if (res.ok) {
        toast.success("Permission updated")
        fetchData()
      } else {
        toast.error("Failed to update")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handleRevoke = async (userId: string) => {
    if (!documentId) return
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/permissions/${userId}`, {
        method: "DELETE",
        headers,
      })
      if (res.ok) {
        toast.success("Permission revoked")
        fetchData()
      } else {
        toast.error("Failed to revoke")
      }
    } catch {
      toast.error("Network error")
    }
  }

  // Filter out users who already have permissions from the dropdown
  const availableUsers = users.filter(u => !permissions.some(p => p.user_id === u.id))

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Document Permissions
          </DialogTitle>
          <DialogDescription>
            Manage which restricted users can access this document. Admins and Employees have automatic access.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="flex items-end gap-4 p-4 border rounded-lg bg-muted/50">
            <div className="space-y-2 flex-1">
              <label className="text-sm font-medium">Select User</label>
              <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a viewer or accountant..." />
                </SelectTrigger>
                <SelectContent>
                  {availableUsers.map(u => (
                    <SelectItem key={u.id} value={u.id}>{u.full_name} ({u.email})</SelectItem>
                  ))}
                  {availableUsers.length === 0 && (
                    <SelectItem value="none" disabled>No eligible users found</SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox id="c_view" checked={canView} onCheckedChange={(c) => setCanView(c as boolean)} />
                <label htmlFor="c_view" className="text-sm font-medium leading-none">View</label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="c_download" checked={canDownload} onCheckedChange={(c) => setCanDownload(c as boolean)} />
                <label htmlFor="c_download" className="text-sm font-medium leading-none">Download</label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="c_edit" checked={canEdit} onCheckedChange={(c) => setCanEdit(c as boolean)} />
                <label htmlFor="c_edit" className="text-sm font-medium leading-none">Edit</label>
              </div>
            </div>
            <Button onClick={handleGrant} disabled={!selectedUserId}>Grant Access</Button>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead className="text-center">View</TableHead>
                  <TableHead className="text-center">Download</TableHead>
                  <TableHead className="text-center">Edit</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">Loading...</TableCell></TableRow>
                ) : permissions.length === 0 ? (
                  <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No custom permissions granted.</TableCell></TableRow>
                ) : (
                  permissions.map(p => (
                    <TableRow key={p.id}>
                      <TableCell>
                        <div className="font-medium">{p.user.full_name}</div>
                        <div className="text-xs text-muted-foreground">{p.user.email}</div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox checked={p.can_view} onCheckedChange={(c) => handleUpdate(p.user_id, { can_view: c as boolean })} />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox checked={p.can_download} onCheckedChange={(c) => handleUpdate(p.user_id, { can_download: c as boolean })} />
                      </TableCell>
                      <TableCell className="text-center">
                        <Checkbox checked={p.can_edit} onCheckedChange={(c) => handleUpdate(p.user_id, { can_edit: c as boolean })} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="icon" className="text-destructive" onClick={() => handleRevoke(p.user_id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
