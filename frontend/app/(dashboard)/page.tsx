"use client"

import {
  BarChart3,
  FileText,
  IndianRupee,
  TrendingUp,
  FilePlus,
  Upload,
  Bot,
  Users,
  Briefcase,
  History
} from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/components/providers/auth-provider"
import { useEffect, useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"

interface DashboardStats {
  monthly_revenue: number
  total_invoices: number
  total_documents: number
  active_customers: number
  active_loans: number
}

interface ActivityLog {
  action: string
  created_at: string
  user_name?: string
}


const quickActions = [
  { title: "Upload Document", icon: Upload, href: "/documents", color: "bg-accent" },
  { title: "Create Invoice", icon: FilePlus, href: "/invoices/generator", color: "bg-primary" },
  { title: "AI Assistant", icon: Bot, href: "/ai", color: "bg-chart-4" },
  { title: "Revenue Dashboard", icon: BarChart3, href: "/revenue", color: "bg-chart-1" },
]

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
    {
      title: "Monthly Revenue",
      value: stats ? `₹${stats.monthly_revenue.toLocaleString()}` : "0",
      description: "Current month",
      icon: IndianRupee,
    },
    {
      title: "Total Invoices",
      value: stats ? stats.total_invoices : "0",
      description: "All time",
      icon: FileText,
    },
    {
      title: "Documents",
      value: stats ? stats.total_documents : "0",
      description: "Active documents",
      icon: Upload,
    },
    {
      title: "Customers",
      value: stats ? stats.active_customers : "0",
      description: "Total customers",
      icon: Users,
    },
    {
      title: "Active Loans",
      value: stats ? stats.active_loans : "0",
      description: "Ongoing bank loans",
      icon: Briefcase,
    }
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight font-[family-name:var(--font-heading)]">
          Dashboard
        </h1>
        <p className="text-muted-foreground mt-1">
          Welcome to Sri Naga Sai ERP. Here&apos;s an overview of your business.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {statCards.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-20 mb-1" />
              ) : (
                <div className="text-2xl font-bold">{stat.value}</div>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions - Hidden for viewers */}
      {roleName !== "viewer" && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Button
                key={action.title}
                variant="outline"
                className="h-auto flex-col gap-3 p-6 hover:shadow-md transition-all duration-200"
                asChild
              >
                <Link href={action.href}>
                  <div className={`rounded-lg p-2.5 ${action.color} text-white`}>
                    <action.icon className="h-5 w-5" />
                  </div>
                  <span className="font-semibold">{action.title}</span>
                </Link>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest system actions and events.</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-[250px]" />
                    <Skeleton className="h-4 w-[200px]" />
                  </div>
                </div>
              ))}
            </div>
          ) : activities.length > 0 ? (
            <div className="space-y-4">
              {activities.map((activity, i) => (
                <div key={i} className="flex items-start gap-4 p-3 rounded-lg border bg-card text-card-foreground shadow-sm">
                  <div className="bg-primary/10 p-2 rounded-full">
                    <History className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium leading-none mb-1">
                      {activity.user_name || "System"} performed {activity.action}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(activity.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
              <TrendingUp className="h-12 w-12 mb-4 opacity-30" />
              <p className="text-sm">No recent activity yet.</p>
              <p className="text-xs mt-1">Actions will appear here as you use the system.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
