"use client"

import { useState, useEffect } from "react"
import { Bell, CheckCircle2 } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { createClient } from "@/utils/supabase/client"
import { toast } from "sonner"

const NOTIFICATIONS_API_BASE = "/api/v1/notifications/"

type Notification = {
  id: string
  title: string
  message: string | null
  is_read: boolean
  created_at: string
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  const fetchNotifications = async () => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) return

      setLoading(true)
      const res = await fetch(NOTIFICATIONS_API_BASE, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setNotifications(data)
      }
    } catch (e) {
      console.error("Failed to fetch notifications", e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const initialFetchTimer = window.setTimeout(() => {
      void fetchNotifications()
    }, 0)
    const interval = window.setInterval(() => {
      void fetchNotifications()
    }, 30000)

    return () => {
      window.clearTimeout(initialFetchTimer)
      window.clearInterval(interval)
    }
  }, [])

  const markAsRead = async (id: string) => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) return

    // Optimistic: flip the badge now, restore the snapshot if the server rejects.
    const snapshot = notifications
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n))

    try {
      const res = await fetch(`${NOTIFICATIONS_API_BASE}${id}/read`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    } catch (e) {
      setNotifications(snapshot)
      toast.error("Could not mark the notification as read.")
      console.error("Failed to mark as read", e)
    }
  }

  const markAllAsRead = async () => {
    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session?.access_token) return

    const snapshot = notifications
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))

    try {
      const res = await fetch(`${NOTIFICATIONS_API_BASE}read-all`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` }
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
    } catch (e) {
      setNotifications(snapshot)
      toast.error("Could not mark all notifications as read.")
      console.error("Failed to mark all as read", e)
    }
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9 relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 h-3 w-3 rounded-full bg-destructive flex items-center justify-center text-[8px] text-white font-bold">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b sticky top-0 bg-background/95 backdrop-blur z-10">
          <DropdownMenuLabel className="p-0 font-semibold text-base">Notifications</DropdownMenuLabel>
          {unreadCount > 0 && (
            <Button variant="ghost" size="sm" onClick={markAllAsRead} className="h-auto p-0 text-xs text-muted-foreground hover:text-primary">
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
              Mark all as read
            </Button>
          )}
        </div>
        <div className="overflow-y-auto py-2">
          {notifications.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              {loading ? "Loading..." : "No notifications"}
            </div>
          ) : (
            notifications.map((n) => (
              <div 
                key={n.id} 
                className={`px-4 py-3 flex flex-col gap-1 cursor-default hover:bg-muted/50 transition-colors ${!n.is_read ? 'bg-primary/5 border-l-2 border-primary' : ''}`}
                onClick={() => !n.is_read && markAsRead(n.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className={`text-sm font-medium leading-none ${!n.is_read ? 'text-foreground' : 'text-foreground/80'}`}>
                    {n.title}
                  </span>
                  <span className="text-[10px] text-muted-foreground whitespace-nowrap pt-0.5">
                    {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                  </span>
                </div>
                {n.message && (
                  <span className={`text-xs ${!n.is_read ? 'text-muted-foreground' : 'text-muted-foreground/70'} line-clamp-2 mt-1`}>
                    {n.message}
                  </span>
                )}
              </div>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
