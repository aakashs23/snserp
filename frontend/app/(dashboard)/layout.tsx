import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { TopBar } from "@/components/top-bar"
import { ChatProvider } from "@/components/providers/chat-provider"
import { AIChatDrawer } from "@/components/ai-chat-drawer"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ChatProvider>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <TopBar />
          <main className="flex-1 overflow-auto p-6 relative">
            {children}
          </main>
        </SidebarInset>
      </SidebarProvider>
      <AIChatDrawer />
    </ChatProvider>
  )
}
