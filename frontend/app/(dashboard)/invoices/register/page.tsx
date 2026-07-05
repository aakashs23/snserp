"use client"

import { useState, useEffect, useCallback } from "react"
import { FilePlus, Eye, Trash2, ArrowUpDown } from "lucide-react"
import Link from "next/link"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/components/providers/auth-provider"

interface Invoice {
  id: string
  invoice_number: string
  customer_id: string
  invoice_date: string
  month_of_supply: string | null
  gross_amount: number | null
  net_amount: number | null
  status: string | null
  payment_date: string | null
  created_at: string
  pdf_storage_path: string | null
  customer?: {
    customer_name: string
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  draft: "secondary",
  sent: "outline",
  paid: "default",
  partially_paid: "default",
  overdue: "destructive",
  cancelled: "destructive",
}

const statusLabel: Record<string, string> = {
  draft: "Draft",
  sent: "Sent",
  paid: "Paid",
  partially_paid: "Partially Paid",
  overdue: "Overdue",
  cancelled: "Cancelled",
}

export default function InvoiceRegisterPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  
  // Filtering and Sorting
  const [statusFilter, setStatusFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [sortBy, setSortBy] = useState("date")
  const [sortOrder, setSortOrder] = useState("desc")
  
  // Delete Dialog state
  const [invoiceToDelete, setInvoiceToDelete] = useState<Invoice | null>(null)

  const { roleName } = useAuth()

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchInvoices = useCallback(async () => {
    try {
      const headers = await getAuthHeaders()
      const url = new URL(`${API_URL}/api/v1/invoices`)
      
      if (statusFilter !== "all") url.searchParams.set("status", statusFilter)
      if (searchQuery) url.searchParams.set("search", searchQuery)
      url.searchParams.set("sort_by", sortBy)
      url.searchParams.set("sort_order", sortOrder)

      const res = await fetch(url.toString(), { headers })
      if (res.ok) {
        setInvoices(await res.json())
      }
    } catch {
      toast.error("Failed to fetch invoices")
    } finally {
      setLoading(false)
    }
  }, [statusFilter, searchQuery, sortBy, sortOrder, getAuthHeaders])

  useEffect(() => {
    const t = setTimeout(() => fetchInvoices(), 300)
    return () => clearTimeout(t)
  }, [fetchInvoices])

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc")
    } else {
      setSortBy(column)
      setSortOrder("desc") // Default to desc for new columns
    }
    setLoading(true)
  }

  const handleStatusChange = async (invoiceId: string, newStatus: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/invoices/${invoiceId}`, {
        method: "PUT",
        headers,
        body: JSON.stringify({ status: newStatus }),
      })
      if (res.ok) {
        toast.success("Invoice status updated")
        fetchInvoices() // Refresh
      } else {
        toast.error("Failed to update invoice status")
      }
    } catch {
      toast.error("Network error while updating status")
    }
  }

  const handleDelete = async () => {
    if (!invoiceToDelete) return
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/invoices/${invoiceToDelete.id}`, {
        method: "DELETE",
        headers,
      })
      if (res.ok) {
        toast.success("Invoice deleted successfully")
        setInvoiceToDelete(null)
        fetchInvoices()
      } else if (res.status === 403) {
        toast.error("Permission denied: You must be an admin to delete invoices.")
        setInvoiceToDelete(null)
      } else {
        toast.error("Failed to delete invoice")
      }
    } catch {
      toast.error("Network error while deleting invoice")
    }
  }

  const handleViewPDF = async (invoiceId: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/invoices/${invoiceId}/pdf`, { headers })
      if (res.ok) {
        const data = await res.json()
        if (data.url) {
          window.open(data.url, "_blank")
        } else {
          toast.error("Could not load PDF URL")
        }
      } else {
        toast.error("PDF not found or not yet generated.")
      }
    } catch {
      toast.error("Network error while trying to view PDF.")
    }
  }

  const formatCurrency = (n: number | null) =>
    n != null
      ? new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(n)
      : "—"

  const formatDate = (d: string | null) =>
    d ? new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—"

  const SortableHead = ({ label, column, alignRight = false }: { label: string; column: string, alignRight?: boolean }) => (
    <TableHead className={alignRight ? "text-right cursor-pointer" : "cursor-pointer"} onClick={() => handleSort(column)}>
      <div className={`flex items-center space-x-1 ${alignRight ? "justify-end" : ""}`}>
        <span>{label}</span>
        <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
      </div>
    </TableHead>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Invoice Register
          </h1>
          <p className="text-muted-foreground mt-1">
            View and manage all generated invoices.
          </p>
        </div>
        {(roleName === "admin" || roleName === "accountant") && (
          <Button asChild>
            <Link href="/invoices/generator">
              <FilePlus className="h-4 w-4 mr-2" />
              New Invoice
            </Link>
          </Button>
        )}
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <Input 
          placeholder="Search invoice # or customer..." 
          className="max-w-sm" 
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setLoading(true); }}
        />
        <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setLoading(true); }}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="partially_paid">Partially Paid</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Invoice #</TableHead>
                <SortableHead label="Date" column="date" />
                <SortableHead label="Customer" column="customer" />
                <SortableHead label="Net Total" column="amount" alignRight={true} />
                <SortableHead label="Status" column="status" />
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-20" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                    No invoices found.
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((inv) => (
                  <TableRow key={inv.id}>
                    <TableCell className="font-medium font-mono">{inv.invoice_number}</TableCell>
                    <TableCell>{formatDate(inv.invoice_date)}</TableCell>
                    <TableCell className="font-medium text-muted-foreground">
                      {inv.customer?.customer_name || "Unknown Customer"}
                    </TableCell>
                    <TableCell className="text-right font-mono font-semibold text-primary">{formatCurrency(inv.net_amount)}</TableCell>
                    <TableCell>
                      {roleName === "admin" || roleName === "employee" ? (
                        <Select
                          defaultValue={inv.status || "draft"}
                          onValueChange={(val) => handleStatusChange(inv.id, val)}
                        >
                          <SelectTrigger className="w-[140px] h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="draft">Draft</SelectItem>
                            <SelectItem value="sent">Sent</SelectItem>
                            <SelectItem value="paid">Paid</SelectItem>
                            <SelectItem value="partially_paid">Partially Paid</SelectItem>
                            <SelectItem value="overdue">Overdue</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge variant={statusVariant[inv.status || "draft"] || "secondary"}>
                          {statusLabel[inv.status || "draft"] || inv.status}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {inv.pdf_storage_path ? (
                          <Button variant="ghost" size="sm" onClick={() => handleViewPDF(inv.id)}>
                            <Eye className="h-4 w-4" />
                            <span className="sr-only">View PDF</span>
                          </Button>
                        ) : (
                          <span className="text-muted-foreground text-xs mx-2">No PDF</span>
                        )}
                        
                        {roleName === "admin" && (
                          <Button variant="ghost" size="sm" onClick={() => setInvoiceToDelete(inv)} className="text-destructive hover:text-destructive hover:bg-destructive/10">
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Delete</span>
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

      <Dialog open={!!invoiceToDelete} onOpenChange={(open) => !open && setInvoiceToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Invoice</DialogTitle>
            <DialogDescription>
              Are you sure you want to completely delete invoice {invoiceToDelete?.invoice_number}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setInvoiceToDelete(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete Permanently</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
