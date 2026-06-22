"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Search, Pencil, Trash2, Eye } from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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

interface Customer {
  id: string
  customer_name: string
  gst_number: string | null
  address: string | null
  email: string | null
  phone: string | null
  bank_name: string | null
  bank_account: string | null
  ifsc_code: string | null
  created_at: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchCustomers = useCallback(async () => {
    try {
      const headers = await getAuthHeaders()
      const url = new URL(`${API_URL}/api/v1/customers`)
      if (search) url.searchParams.set("search", search)
      const res = await fetch(url.toString(), { headers })
      if (res.ok) {
        const data = await res.json()
        setCustomers(data)
      }
    } catch (err) {
      toast.error("Failed to fetch customers")
    } finally {
      setLoading(false)
    }
  }, [search, getAuthHeaders])

  useEffect(() => {
    fetchCustomers()
  }, [fetchCustomers])

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const body = Object.fromEntries(formData.entries())

    // Remove empty strings
    for (const key of Object.keys(body)) {
      if (body[key] === "") delete body[key]
    }

    try {
      const headers = await getAuthHeaders()
      const url = editingCustomer
        ? `${API_URL}/api/v1/customers/${editingCustomer.id}`
        : `${API_URL}/api/v1/customers`
      const method = editingCustomer ? "PUT" : "POST"

      const res = await fetch(url, { method, headers, body: JSON.stringify(body) })
      if (res.ok) {
        toast.success(editingCustomer ? "Customer updated" : "Customer created")
        setDialogOpen(false)
        setEditingCustomer(null)
        fetchCustomers()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Operation failed")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/customers/${id}`, { method: "DELETE", headers })
      if (res.ok) {
        toast.success("Customer deleted")
        setDeleteConfirm(null)
        fetchCustomers()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to delete")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const openEdit = (customer: Customer) => {
    setEditingCustomer(customer)
    setDialogOpen(true)
  }

  const openNew = () => {
    setEditingCustomer(null)
    setDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Customers
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your customer database.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setEditingCustomer(null); }}>
          <DialogTrigger asChild>
            <Button onClick={openNew}>
              <Plus className="h-4 w-4 mr-2" />
              Add Customer
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[550px]">
            <form onSubmit={handleSubmit}>
              <DialogHeader>
                <DialogTitle>{editingCustomer ? "Edit Customer" : "Add Customer"}</DialogTitle>
                <DialogDescription>
                  {editingCustomer ? "Update customer information." : "Enter the new customer\u2019s details."}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="customer_name">Customer Name *</Label>
                    <Input id="customer_name" name="customer_name" required defaultValue={editingCustomer?.customer_name ?? ""} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gst_number">GST Number</Label>
                    <Input id="gst_number" name="gst_number" defaultValue={editingCustomer?.gst_number ?? ""} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" name="email" type="email" defaultValue={editingCustomer?.email ?? ""} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input id="phone" name="phone" defaultValue={editingCustomer?.phone ?? ""} />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input id="address" name="address" defaultValue={editingCustomer?.address ?? ""} />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="bank_name">Bank Name</Label>
                    <Input id="bank_name" name="bank_name" defaultValue={editingCustomer?.bank_name ?? ""} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank_account">Account No.</Label>
                    <Input id="bank_account" name="bank_account" defaultValue={editingCustomer?.bank_account ?? ""} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="ifsc_code">IFSC Code</Label>
                    <Input id="ifsc_code" name="ifsc_code" defaultValue={editingCustomer?.ifsc_code ?? ""} />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit">{editingCustomer ? "Save Changes" : "Create Customer"}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search customers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>GST Number</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-36" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : customers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-12 text-muted-foreground">
                    No customers found. Click &ldquo;Add Customer&rdquo; to get started.
                  </TableCell>
                </TableRow>
              ) : (
                customers.map((customer) => (
                  <TableRow key={customer.id}>
                    <TableCell className="font-medium">{customer.customer_name}</TableCell>
                    <TableCell className="text-muted-foreground">{customer.gst_number || "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{customer.email || "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{customer.phone || "—"}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(customer)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        {deleteConfirm === customer.id ? (
                          <Button variant="destructive" size="sm" className="h-8" onClick={() => handleDelete(customer.id)}>
                            Confirm
                          </Button>
                        ) : (
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => setDeleteConfirm(customer.id)}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
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
  )
}
