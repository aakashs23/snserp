"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Pencil, Trash2, Calendar, IndianRupee, PieChart, TrendingUp, Table as TableIcon } from "lucide-react"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface Loan {
  id: string
  loan_name: string
  bank_name: string
  principal_amount: number
  interest_rate_annual: number
  tenure_months: number
  payment_frequency: string
  start_date: string
  status: string
}

interface DashboardMetrics {
  outstanding_balance: number
  total_interest_remaining: number
  total_emi_remaining: number
  total_emi_paid: number
  next_due_date: string | null
}

interface AmortizationRow {
  installment: number
  date: string
  emi: number
  principal: number
  interest: number
  remaining_balance: number
}

import { RoleGuard } from "@/components/role-guard"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function LoansPage() {
  const [loans, setLoans] = useState<Loan[]>([])
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingLoan, setEditingLoan] = useState<Loan | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const [amortizationOpen, setAmortizationOpen] = useState(false)
  const [amortizationData, setAmortizationData] = useState<AmortizationRow[]>([])
  const [amortizationLoading, setAmortizationLoading] = useState(false)
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null)

  const getAuthHeaders = useCallback(async () => {
    const supabase = createClient()
    const {
      data: { session },
    } = await supabase.auth.getSession()

    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.access_token}`,
    }
  }, [])

  const fetchData = useCallback(async () => {
    try {
      const headers = await getAuthHeaders()
      const [loansRes, metricsRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/loans`, { headers }),
        fetch(`${API_URL}/api/v1/loans/dashboard`, { headers }),
      ])

      if (loansRes.ok) {
        setLoans(await loansRes.json())
      }
      if (metricsRes.ok) {
        setMetrics(await metricsRes.json())
      }
    } catch {
      toast.error("Failed to fetch loans data")
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
    const body = Object.fromEntries(formData.entries())
    const payload = {
      ...body,
      principal_amount: parseFloat(body.principal_amount as string),
      interest_rate_annual: parseFloat(body.interest_rate_annual as string),
      tenure_months: parseInt(body.tenure_months as string),
    }

    try {
      const headers = await getAuthHeaders()
      const url = editingLoan
        ? `${API_URL}/api/v1/loans/${editingLoan.id}`
        : `${API_URL}/api/v1/loans`
      const method = editingLoan ? "PUT" : "POST"

      const res = await fetch(url, { method, headers, body: JSON.stringify(payload) })

      if (res.ok) {
        toast.success(editingLoan ? "Loan updated" : "Loan created")
        setDialogOpen(false)
        setEditingLoan(null)
        fetchData()
      } else {
        const err = await res.json()
        let errorMessage = "Operation failed."

        if (err.detail) {
          if (Array.isArray(err.detail)) {
            errorMessage = err.detail
              .map((entry: any) => `${entry.loc?.join(".")} - ${entry.msg}`)
              .join(", ")
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

  const handleDelete = async (id: string) => {
    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/loans/${id}`, { method: "DELETE", headers })

      if (res.ok) {
        toast.success("Loan deleted")
        setDeleteConfirm(null)
        fetchData()
      } else {
        const err = await res.json()
        toast.error(err.detail || "Failed to delete")
      }
    } catch {
      toast.error("Network error")
    }
  }

  const handleViewAmortization = async (loan: Loan) => {
    setSelectedLoan(loan)
    setAmortizationOpen(true)
    setAmortizationLoading(true)

    try {
      const headers = await getAuthHeaders()
      const res = await fetch(`${API_URL}/api/v1/loans/${loan.id}/amortization`, { headers })

      if (res.ok) {
        const data = await res.json()
        setAmortizationData(data.schedule)
      } else {
        toast.error("Failed to load schedule")
      }
    } catch {
      toast.error("Network error")
    } finally {
      setAmortizationLoading(false)
    }
  }

  const openEdit = (loan: Loan) => {
    setEditingLoan(loan)
    setDialogOpen(true)
  }

  const openNew = () => {
    setEditingLoan(null)
    setDialogOpen(true)
  }

  const formatCurrency = (n: number | null | undefined) =>
    n != null
      ? new Intl.NumberFormat("en-IN", {
          style: "currency",
          currency: "INR",
          maximumFractionDigits: 0,
        }).format(n)
      : "—"

  return (
    <RoleGuard allowedRoles={["admin", "employee"]}>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
              Loan Management
            </h1>
            <p className="text-muted-foreground mt-1">
              Track bank loans and amortization schedules.
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) setEditingLoan(null); }}>
            <DialogTrigger asChild>
              <Button onClick={openNew}>
                <Plus className="h-4 w-4 mr-2" />
                Add Loan
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[550px]">
              <form onSubmit={handleSubmit}>
                <DialogHeader>
                  <DialogTitle>{editingLoan ? "Edit Loan" : "Add Loan"}</DialogTitle>
                  <DialogDescription>
                    {editingLoan ? "Update loan information." : "Enter the new loan details."}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="loan_name">Loan Name *</Label>
                      <Input id="loan_name" name="loan_name" required defaultValue={editingLoan?.loan_name ?? ""} placeholder="e.g. Solar Plant Term Loan" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bank_name">Bank Name *</Label>
                      <Input id="bank_name" name="bank_name" required defaultValue={editingLoan?.bank_name ?? ""} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="principal_amount">Principal Amount (₹) *</Label>
                      <Input id="principal_amount" name="principal_amount" type="number" step="0.01" required defaultValue={editingLoan?.principal_amount ?? ""} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="interest_rate_annual">Annual Interest Rate (%) *</Label>
                      <Input id="interest_rate_annual" name="interest_rate_annual" type="number" step="0.01" required defaultValue={editingLoan?.interest_rate_annual ?? ""} />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="tenure_months">Tenure (Months) *</Label>
                      <Input id="tenure_months" name="tenure_months" type="number" required defaultValue={editingLoan?.tenure_months ?? ""} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="start_date">Start Date *</Label>
                      <Input id="start_date" name="start_date" type="date" required defaultValue={editingLoan?.start_date ?? ""} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="payment_frequency">Frequency</Label>
                      <Select name="payment_frequency" defaultValue={editingLoan?.payment_frequency ?? "monthly"}>
                        <SelectTrigger>
                          <SelectValue placeholder="Monthly" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="monthly">Monthly</SelectItem>
                          <SelectItem value="quarterly">Quarterly</SelectItem>
                          <SelectItem value="annual">Annual</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit">{editingLoan ? "Save Changes" : "Create Loan"}</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Dashboard Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-primary/5 border-primary/20">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding Balance</CardTitle>
              <IndianRupee className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? <Skeleton className="h-8 w-24" /> : formatCurrency(metrics?.outstanding_balance)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Total remaining principal across active loans</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Interest Remaining</CardTitle>
              <PieChart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? <Skeleton className="h-8 w-24" /> : formatCurrency(metrics?.total_interest_remaining)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Future interest payments</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Next Due Date</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? <Skeleton className="h-8 w-24" /> : (metrics?.next_due_date || "—")}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Earliest upcoming payment</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total EMI Paid</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-600">
                {loading ? <Skeleton className="h-8 w-24" /> : formatCurrency(metrics?.total_emi_paid)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Payments made historically</p>
            </CardContent>
          </Card>
        </div>

        {/* Table */}
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loan Name</TableHead>
                  <TableHead>Bank</TableHead>
                  <TableHead className="text-right">Principal</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead>Tenure</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-20" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : loans.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      No loans found. Click &quot;Add Loan&quot; to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  loans.map((loan) => (
                    <TableRow key={loan.id}>
                      <TableCell className="font-medium">{loan.loan_name}</TableCell>
                      <TableCell>{loan.bank_name}</TableCell>
                      <TableCell className="text-right font-mono">{formatCurrency(loan.principal_amount)}</TableCell>
                      <TableCell className="text-right">{loan.interest_rate_annual}%</TableCell>
                      <TableCell>{loan.tenure_months} months</TableCell>
                      <TableCell>{loan.start_date}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="outline" size="sm" onClick={() => handleViewAmortization(loan)}>
                            <TableIcon className="h-4 w-4 mr-2" />
                            Schedule
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 ml-2" onClick={() => openEdit(loan)}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          {deleteConfirm === loan.id ? (
                            <Button variant="destructive" size="sm" className="h-8" onClick={() => handleDelete(loan.id)}>
                              Confirm
                            </Button>
                          ) : (
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => setDeleteConfirm(loan.id)}>
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

        {/* Amortization Modal */}
        <Dialog open={amortizationOpen} onOpenChange={setAmortizationOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] flex flex-col">
            <DialogHeader>
              <DialogTitle>Amortization Schedule</DialogTitle>
              <DialogDescription>
                {selectedLoan?.loan_name} - {selectedLoan?.bank_name} ({selectedLoan?.tenure_months} months @ {selectedLoan?.interest_rate_annual}%)
              </DialogDescription>
            </DialogHeader>
            
            <div className="flex-1 overflow-auto border rounded-md mt-4">
              <Table>
                <TableHeader className="bg-muted sticky top-0 z-10">
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">EMI</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">Remaining Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {amortizationLoading ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8">
                        Loading schedule...
                      </TableCell>
                    </TableRow>
                  ) : (
                    amortizationData.map((row) => (
                      <TableRow key={row.installment}>
                        <TableCell>{row.installment}</TableCell>
                        <TableCell>{row.date}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(row.emi)}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(row.principal)}</TableCell>
                        <TableCell className="text-right font-mono text-destructive">{formatCurrency(row.interest)}</TableCell>
                        <TableCell className="text-right font-mono font-medium">{formatCurrency(row.remaining_balance)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </RoleGuard>
  )
}
