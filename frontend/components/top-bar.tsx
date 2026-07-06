"use client"

import { Bell, Sparkles } from "lucide-react"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { useChat } from "@/components/providers/chat-provider"
import { NotificationCenter } from "@/components/notification-center"

export function TopBar() {
  const { toggleChat } = useChat()

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b bg-background/80 backdrop-blur-sm px-4">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />

      {/* Breadcrumb area — future enhancement */}
      <div className="flex-1" />

      {/* Right side actions */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" className="h-9 w-9 relative" onClick={toggleChat} title="AI Assistant">
          <Sparkles className="h-4.5 w-4.5 text-primary" />
        </Button>
        <NotificationCenter />
        <ThemeToggle />
      </div>
    </header>
  )
}
