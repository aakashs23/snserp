"use client"

import { useState, useEffect, useCallback } from "react"
import { BarChart3, FileText, CheckCircle2, Clock } from "lucide-react"
import { toast } from "sonner"
import { createClient } from "@/utils/supabase/client"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from "recharts"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { RoleGuard } from "@/components/role-guard"

interface MonthlyRevenueItem {
  month: string
  revenue: number
  paid: number
  pending: number
}

interface TopCustomerItem {
  customer_name: string
  revenue: number
}

interface RevenueData {
  total_revenue_ytd: number
  total_invoices_generated: number
  pending_invoices_count: number
  paid_invoices_count: number
  monthly_trend: MonthlyRevenueItem[]
  top_customers: TopCustomerItem[]
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function RevenueDashboardPage() {
  const [data, setData] = useState<RevenueData | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAnalytics = useCallback(async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      
      const res = await fetch(`${API_URL}/api/v1/analytics/revenue`, {
        headers: {
          "Authorization": `Bearer ${session?.access_token}`,
          "Content-Type": "application/json"
        }
      })
      
      if (res.ok) {
        setData(await res.json())
      } else {
        toast.error("Failed to load revenue data")
      }
    } catch {
      toast.error("Network error")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => fetchAnalytics(), 0)
    return () => clearTimeout(t)
  }, [fetchAnalytics])

  const formatCurrency = (n: number) => 
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n)

  if (loading) {
    return (
      <RoleGuard allowedRoles={["admin", "employee"]}>
        <div className="space-y-6">
          <h1 className="text-3xl font-bold tracking-tight">Revenue Dashboard</h1>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <Skeleton className="lg:col-span-4 h-[400px] rounded-xl" />
            <Skeleton className="lg:col-span-3 h-[400px] rounded-xl" />
          </div>
        </div>
      </RoleGuard>
    )
  }

  if (!data) {
    return (
      <RoleGuard allowedRoles={["admin", "employee"]}>
        <div>Error loading data.</div>
      </RoleGuard>
    )
  }

  return (
    <RoleGuard allowedRoles={["admin", "employee"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
            Revenue Dashboard
          </h1>
          <p className="text-muted-foreground mt-1">
            Financial overview and analytics for {new Date().getFullYear()}.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Revenue YTD</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(data.total_revenue_ytd)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Invoices Generated</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{data.total_invoices_generated}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Paid Invoices</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{data.paid_invoices_count}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Pending Invoices</CardTitle>
              <Clock className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-amber-500">{data.pending_invoices_count}</div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="lg:col-span-4">
            <CardHeader>
              <CardTitle>Monthly Revenue Trend</CardTitle>
              <CardDescription>Gross revenue grouped by month of supply.</CardDescription>
            </CardHeader>
            <CardContent className="pl-2">
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.monthly_trend} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="month" axisLine={false} tickLine={false} tickMargin={10} />
                    <YAxis axisLine={false} tickLine={false} tickFormatter={(value) => `₹${value / 1000}k`} />
                    <RechartsTooltip 
                      formatter={(value: unknown) => formatCurrency(Number(value))}
                      cursor={{ stroke: 'var(--border)', strokeWidth: 1 }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <Line type="monotone" dataKey="revenue" stroke="hsl(var(--primary))" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Top Customers</CardTitle>
              <CardDescription>Highest revenue generating customers.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.top_customers} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                    <XAxis type="number" axisLine={false} tickLine={false} tickFormatter={(value) => `₹${value / 1000}k`} />
                    <YAxis dataKey="customer_name" type="category" axisLine={false} tickLine={false} width={100} />
                    <RechartsTooltip 
                      formatter={(value: unknown) => formatCurrency(Number(value))}
                      cursor={{ fill: 'hsl(var(--accent)/0.1)' }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <Bar dataKey="revenue" fill="hsl(var(--accent))" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </RoleGuard>
  )
}
