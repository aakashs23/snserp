"use client"

import {
  BarChart3,
  FileText,
  IndianRupee,
  FilePlus,
  Upload,
  Users,
  Briefcase,
  History,
  Activity,
  CheckCircle2,
  Clock,
  AlertCircle
} from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/components/providers/auth-provider"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts"

interface DashboardStats {
  monthly_revenue: number
  yearly_revenue: number
  total_customers: number
  total_documents: number
  total_invoices: number
  paid_invoices: number
  pending_invoices: number
  outstanding_amount: number
  active_loans: number
  recent_uploads: number

  revenue_trend: any[]
  invoice_status: any[]
  revenue_by_customer: any[]
  documents_uploaded_per_month: any[]
  recent_revenue_trend: any[]
}

interface ActivityLog {
  action: string
  created_at: string
  user_name?: string
  module?: string
  object_affected?: string
}

const quickActions = [
  { title: "Upload Document", icon: Upload, href: "/documents", color: "bg-accent" },
  { title: "Create Invoice", icon: FilePlus, href: "/invoices/generator", color: "bg-primary" },
  { title: "Revenue Dashboard", icon: BarChart3, href: "/revenue", color: "bg-chart-1" },
]

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

export default function DashboardPage() {
  const { roleName } = useAuth()
  
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<ActivityLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const token = localStorage.getItem("token")
        const headers = {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        }
        const [statsRes, activityRes] = await Promise.all([
          fetch(`${API_URL}/api/v1/analytics/dashboard/stats`, { headers }),
          fetch(`${API_URL}/api/v1/analytics/dashboard/activity`, { headers })
        ])
        
        if (statsRes.ok && activityRes.ok) {
          setStats(await statsRes.json())
          setActivities(await activityRes.json())
        }
      } catch (error) {
        console.error("Error fetching dashboard data:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const statCards = [
    { title: "Monthly Revenue", value: stats ? `₹${stats.monthly_revenue.toLocaleString()}` : "0", description: "Current month", icon: IndianRupee },
    { title: "Yearly Revenue", value: stats ? `₹${stats.yearly_revenue.toLocaleString()}` : "0", description: "YTD", icon: IndianRupee },
    { title: "Outstanding Amount", value: stats ? `₹${stats.outstanding_amount.toLocaleString()}` : "0", description: "Unpaid invoices", icon: AlertCircle },
    { title: "Total Invoices", value: stats ? stats.total_invoices : "0", description: "All time", icon: FileText },
    { title: "Paid Invoices", value: stats ? stats.paid_invoices : "0", description: "Completed", icon: CheckCircle2 },
    { title: "Pending Invoices", value: stats ? stats.pending_invoices : "0", description: "Awaiting payment", icon: Clock },
    { title: "Customers", value: stats ? stats.total_customers : "0", description: "Total clients", icon: Users },
    { title: "Documents", value: stats ? stats.total_documents : "0", description: "Total files", icon: FileText },
    { title: "Recent Uploads", value: stats ? stats.recent_uploads : "0", description: "Last 7 days", icon: Upload },
    { title: "Active Loans", value: stats ? stats.active_loans : "0", description: "Ongoing", icon: Briefcase }
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
          Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Welcome to Sri Naga Sai ERP. Here&apos;s a live overview of your business.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-20 mb-1" />
              ) : (
                <div className="text-2xl font-bold">{stat.value}</div>
              )}
              <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Section */}
      {!loading && stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
          
          <Card>
            <CardHeader>
              <CardTitle>Revenue Trend (Monthly)</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={stats.revenue_trend}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(val: any) => `₹${Number(val).toLocaleString()}`} />
                  <Line type="monotone" dataKey="revenue" stroke="#8884d8" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Revenue Trend (7 Days)</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.recent_revenue_trend}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip formatter={(val: any) => `₹${Number(val).toLocaleString()}`} />
                  <Area type="monotone" dataKey="revenue" stroke="#00C49F" fill="#00C49F" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Revenue by Customer (Top 5)</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.revenue_by_customer} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" />
                  <YAxis dataKey="customer_name" type="category" width={100} />
                  <Tooltip formatter={(val: any) => `₹${Number(val).toLocaleString()}`} />
                  <Bar dataKey="revenue" fill="#FFBB28" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Invoice Status</CardTitle>
              </CardHeader>
              <CardContent className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={stats.invoice_status} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} label>
                      {stats.invoice_status.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Documents Uploaded</CardTitle>
              </CardHeader>
              <CardContent className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.documents_uploaded_per_month}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0088FE" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Bottom Section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Quick Actions */}
        {roleName !== "viewer" && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)]">
              Quick Actions
            </h2>
            <div className="grid gap-3">
              {quickActions.map((action) => (
                <Link key={action.title} href={action.href}>
                  <Card className="hover:border-primary/50 transition-colors">
                    <CardHeader className="p-4 flex flex-row items-center gap-4 space-y-0">
                      <div className={`p-2 rounded-lg ${action.color} text-primary-foreground`}>
                        <action.icon className="h-5 w-5" />
                      </div>
                      <CardTitle className="text-base">{action.title}</CardTitle>
                    </CardHeader>
                  </Card>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Activity Logs */}
        <div className={`space-y-4 ${roleName !== "viewer" ? "lg:col-span-2" : "lg:col-span-3"}`}>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold font-[family-name:var(--font-heading)] flex items-center gap-2">
              <Activity className="h-5 w-5 text-primary" />
              Recent Activity
            </h2>
            <Link href="/activity">
              <Button variant="ghost" size="sm" className="text-muted-foreground">
                View All
              </Button>
            </Link>
          </div>
          
          <Card>
            <CardContent className="p-0">
              <div className="divide-y">
                {loading ? (
                  Array(5).fill(0).map((_, i) => (
                    <div key={i} className="p-4 flex items-center gap-4">
                      <Skeleton className="h-10 w-10 rounded-full" />
                      <div className="space-y-2 flex-1">
                        <Skeleton className="h-4 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                      </div>
                    </div>
                  ))
                ) : activities.length > 0 ? (
                  activities.map((activity, i) => (
                    <div key={i} className="p-4 flex items-center justify-between hover:bg-muted/50 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-medium">
                          {activity.user_name?.[0]?.toUpperCase() || "U"}
                        </div>
                        <div>
                          <p className="text-sm font-medium leading-none mb-1">
                            {activity.action} <span className="text-muted-foreground font-normal">in {activity.module}</span>
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {activity.user_name || "Unknown User"} • {activity.object_affected || ""}
                          </p>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(activity.created_at).toLocaleDateString()} {new Date(activity.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    No recent activity found.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
